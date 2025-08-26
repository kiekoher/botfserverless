const test = require('node:test');
const assert = require('node:assert');
const { mock } = require('node:test');
const Module = require('module');

// --- Environment Setup ---
process.env.NODE_ENV = 'test';
process.env.WHATSAPP_USER_ID = 'user1';
process.env.MAIN_API_URL = 'http://mock-api/api/v1/messages/whatsapp';
process.env.R2_ENDPOINT_URL = 'http://example.com';
process.env.R2_BUCKET_NAME = 'bucket';
process.env.R2_ACCESS_KEY_ID = 'access';
process.env.R2_SECRET_ACCESS_KEY = 'secret';

// --- Mocks for External Modules ---
const axios = {
  post: mock.fn(async () => ({ status: 202, data: {} })),
};

const s3Send = mock.fn(async () => {});
class S3Client {
  constructor() { this.send = s3Send; }
}

class Client {
  constructor() { this.handlers = {}; }
  on(event, handler) { this.handlers[event] = handler; }
  async initialize() {}
  async getState() { return 'CONNECTED'; }
}

// --- Monkey-patching Node's module loader for deep mocking ---
const originalLoad = Module._load;
const mockedLoad = function (request, parent, isMain) {
  if (request === 'axios') return axios;
  if (request === '@aws-sdk/client-s3') return { S3Client, PutObjectCommand: class {} };
  if (request === 'whatsapp-web.js') return { Client, LocalAuth: class {} };
  if (request === 'qrcode-terminal') return { generate: () => {} };

  if (request === 'pino') {
    const pinoMock = () => ({ info: () => {}, error: () => {}, warn: () => {} });
    // Mock the transport property to avoid TypeError during initialization
    pinoMock.transport = () => {};
    return pinoMock;
  }

  if (request === 'prom-client') {
    return {
      collectDefaultMetrics: () => {},
      Gauge: class { set() {} },
      register: { contentType: '', metrics: async () => '' },
    };
  }
  if (request === 'http') return { createServer: () => ({ listen: () => {} }) };
  if (request === 'uuid') return { v4: () => 'mock-uuid' };
  if (request === 'dotenv') return { config: () => {} };

  return originalLoad(request, parent, isMain);
};
Module._load = mockedLoad;

// --- Test Suite ---
test.beforeEach(() => {
  // Reset mocks before each test
  axios.post.mock.resetCalls();
  s3Send.mock.resetCalls();
});

// Import the bot module AFTER mocks are set up
const bot = require('../bot.js');
const messageHandler = bot.client.handlers['message'];

function createMockMessage(overrides = {}) {
  const message = {
    from: '1234567890',
    body: 'Hello, world!',
    hasMedia: false,
    timestamp: Date.now() / 1000,
    getChat: async () => ({ isGroup: false, sendStateTyping: () => {} }),
    getContact: async () => ({ pushname: 'John Doe' }),
    reply: mock.fn(async () => {}),
    downloadMedia: mock.fn(async () => {}),
    ...overrides,
  };
  return message;
}

test('handles a simple text message', async () => {
  const msg = createMockMessage();

  await messageHandler(msg);

  assert.strictEqual(axios.post.mock.calls.length, 1, 'axios.post should be called once');

  const [url, payload] = axios.post.mock.calls[0].arguments;
  assert.strictEqual(url, process.env.MAIN_API_URL);
  assert.strictEqual(payload.body, 'Hello, world!');
  assert.strictEqual(payload.userId, '1234567890');
  assert.strictEqual(payload.mediaKey, '');
});

test('handles an audio message and uploads to R2', async () => {
  const audioData = Buffer.from('fake-audio-data').toString('base64');
  const msg = createMockMessage({
    hasMedia: true,
    downloadMedia: async () => ({ mimetype: 'audio/ogg', data: audioData }),
  });

  await messageHandler(msg);

  assert.strictEqual(s3Send.mock.calls.length, 1, 'S3 send should be called for audio');
  assert.strictEqual(axios.post.mock.calls.length, 1, 'axios.post should be called after upload');

  const [url, payload] = axios.post.mock.calls[0].arguments;
  assert.strictEqual(payload.mediaType, 'audio/ogg');
  assert.strictEqual(payload.mediaKey.endsWith('.ogg'), true);
});

test('rejects audio messages that are too large', async () => {
  const largeAudioData = Buffer.alloc(11 * 1024 * 1024).toString('base64'); // 11MB
  const msg = createMockMessage({
    hasMedia: true,
    downloadMedia: async () => ({ mimetype: 'audio/ogg', data: largeAudioData }),
  });

  await messageHandler(msg);

  assert.strictEqual(msg.reply.mock.calls.length, 1, 'Should reply with an error message');
  assert.strictEqual(msg.reply.mock.calls[0].arguments[0], 'Audio file is too large. Max 10MB.');
  assert.strictEqual(axios.post.mock.calls.length, 0, 'axios.post should not be called for oversized media');
});

test('handles non-audio media by replying with an error', async () => {
  const msg = createMockMessage({
    hasMedia: true,
    downloadMedia: async () => ({ mimetype: 'image/jpeg', data: 'fake-image' }),
  });

  await messageHandler(msg);

  assert.strictEqual(msg.reply.mock.calls.length, 1, 'Should reply with an error message');
  assert.strictEqual(axios.post.mock.calls.length, 0, 'axios.post should not be called for non-audio media');
});

test('handles errors during API call by replying to the user', async () => {
  axios.post.mock.mockImplementationOnce(async () => {
    throw new Error('API is down');
  });

  const msg = createMockMessage();
  await messageHandler(msg);

  assert.strictEqual(msg.reply.mock.calls.length, 1, 'Should reply with an error on API failure');
  assert.strictEqual(msg.reply.mock.calls[0].arguments[0], "I'm having trouble processing your message. Please try again later.");
});
