const test = require('node:test');
const assert = require('node:assert');
const { mock } = require('node:test');
const Module = require('module');

process.env.NODE_ENV = 'test';
process.env.WHATSAPP_USER_ID = 'user1';
process.env.R2_ENDPOINT_URL = 'http://example.com';
process.env.R2_BUCKET_NAME = 'bucket';
process.env.R2_ACCESS_KEY_ID = 'access';
process.env.R2_SECRET_ACCESS_KEY = 'secret';

// Mocks for external modules
const redisClient = {
  connect: mock.fn(async () => {}),
  on: () => {},
  xAdd: mock.fn(async () => {}),
  set: mock.fn(async () => {}),
  del: mock.fn(async () => {}),
  isOpen: true,
  xGroupCreate: mock.fn(async () => {}),
  xReadGroup: mock.fn(async () => []),
  xAck: mock.fn(async () => {}),
};

const s3Send = mock.fn(async () => {});
class S3Client {
  constructor() { this.send = s3Send; }
}

class Client {
  constructor() { this.handlers = {}; }
  on(event, handler) { this.handlers[event] = handler; }
  async initialize() {}
}
const originalLoad = Module._load;
const mockedLoad = function (request, parent, isMain) {
  if (request === 'redis') return { createClient: () => redisClient };
  if (request === '@aws-sdk/client-s3') return { S3Client, PutObjectCommand: class {} };
  if (request === 'whatsapp-web.js') return { Client, LocalAuth: class {} };
  if (request === 'qrcode-terminal') return { generate: () => {} };
  if (request === 'prom-client') {
    return {
      collectDefaultMetrics: () => {},
      Gauge: class { set() {} },
      register: { contentType: '', metrics: async () => '' },
    };
  }
  if (request === 'pino') return () => ({ info: () => {}, error: () => {} });
  if (request === 'http') return { createServer: () => ({ listen: () => {} }) };
  if (request === 'uuid') return { v4: () => 'uuid' };
  if (request === 'dotenv') return { config: () => {} };
  return originalLoad(request, parent, isMain);
};
Module._load = mockedLoad;

const bot = require('../bot.js');
const handler = bot.client.handlers['message'];

function baseMessage(overrides = {}) {
  return {
    from: '123',
    body: 'hi',
    hasMedia: false,
    timestamp: 1,
    getChat: async () => ({ isGroup: false, sendStateTyping: () => {} }),
    reply: mock.fn(async () => {}),
    ...overrides,
  };
}

test('handles text message', async () => {
  const msg = baseMessage();
  await handler(msg);
  assert.strictEqual(redisClient.xAdd.mock.calls.length, 1);
  const payload = redisClient.xAdd.mock.calls[0].arguments[2];
  assert.strictEqual(payload.body, 'hi');
});

test('handles audio message', async () => {
  const audioData = Buffer.from('small').toString('base64');
  const msg = baseMessage({
    hasMedia: true,
    downloadMedia: async () => ({ mimetype: 'audio/ogg', data: audioData }),
  });
  await handler(msg);
  assert.strictEqual(s3Send.mock.calls.length, 1);
});

test('rejects large audio', async () => {
  const large = Buffer.alloc(10 * 1024 * 1024 + 1).toString('base64');
  const msg = baseMessage({
    hasMedia: true,
    downloadMedia: async () => ({ mimetype: 'audio/ogg', data: large }),
  });
  await handler(msg);
  assert.strictEqual(msg.reply.mock.calls.length, 1);
  assert.strictEqual(redisClient.xAdd.mock.calls.length, 2); // only previous successes
});

test('handles redis error', async () => {
  const errorClient = {
    ...redisClient,
    xAdd: mock.fn(async () => { throw new Error('fail'); }),
  };
  Module._load = function (request, parent, isMain) {
    if (request === 'redis') return { createClient: () => errorClient };
    return mockedLoad(request, parent, isMain);
  };
  delete require.cache[require.resolve('../bot.js')];
  const bot2 = require('../bot.js');
  const handler2 = bot2.client.handlers['message'];
  const msg = baseMessage();
  await handler2(msg);
  assert.strictEqual(msg.reply.mock.calls.length, 1);
  Module._load = mockedLoad;
});
