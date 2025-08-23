require('dotenv').config();
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const { createClient } = require('redis');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { v4: uuidv4 } = require('uuid');

// --- Configuration ---
const REDIS_HOST = process.env.REDIS_HOST || 'redis';
const STREAM_IN = 'events:new_message';
const STREAM_OUT = 'events:message_out';
const CONSUMER_GROUP = 'group:whatsapp-gateway';
const CONSUMER_NAME = 'consumer:whatsapp-gateway-1';

// R2 Configuration
const R2_ENDPOINT_URL = process.env.R2_ENDPOINT_URL; // e.g., https://<accountid>.r2.cloudflarestorage.com
const R2_BUCKET_NAME = process.env.R2_BUCKET_NAME;
const R2_ACCESS_KEY_ID = process.env.R2_ACCESS_KEY_ID;
const R2_SECRET_ACCESS_KEY = process.env.R2_SECRET_ACCESS_KEY;
const R2_REGION = process.env.R2_REGION || "auto";

// --- Initialize Clients ---
console.log("🤖 WhatsApp Gateway Initializing...");

// Redis Client with retry logic
const redisClient = createClient({ url: `redis://${REDIS_HOST}:6379` });
redisClient.on('error', (err) => console.error('Redis Client Error', err));

async function connectRedis(retry = 0) {
    const delay = Math.min(1000 * 2 ** retry, 30000);
    try {
        await redisClient.connect();
        console.log('🔌 Connected to Redis.');
    } catch (err) {
        console.error('❌ Redis connection error:', err);
        await new Promise((res) => setTimeout(res, delay));
        return connectRedis(retry + 1);
    }
}

connectRedis();

// S3 Client for R2
const s3Client = new S3Client({
    endpoint: R2_ENDPOINT_URL,
    region: R2_REGION,
    credentials: {
        accessKeyId: R2_ACCESS_KEY_ID,
        secretAccessKey: R2_SECRET_ACCESS_KEY,
    },
});
console.log("☁️  R2 S3 Client Initialized.");

// WhatsApp Client
const SESSION_PATH = process.env.WHATSAPP_SESSION_PATH || '/session';
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: SESSION_PATH }),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
    }
});

async function initializeClient(retry = 0) {
    const delay = Math.min(1000 * 2 ** retry, 30000);
    try {
        await client.initialize();
    } catch (err) {
        console.error('❌ WhatsApp init error:', err);
        await new Promise((res) => setTimeout(res, delay));
        return initializeClient(retry + 1);
    }
}

client.on('disconnected', async (reason) => {
    console.error(`⚠️ WhatsApp disconnected: ${reason}. Reinitializing...`);
    await initializeClient();
});

// --- Event Handlers ---
client.on('qr', async (qr) => {
    console.log('📱 Scan QR code to connect:');
    qrcode.generate(qr, { small: true });
    // Store the QR code in Redis for the main API to fetch
    try {
        await redisClient.set('whatsapp:qr_code', qr, { EX: 60 }); // Expires in 60 seconds
        console.log('큐알코드를 레디스에 성공적으로 저장했습니다');
        await redisClient.set('whatsapp:status', 'disconnected');
    } catch (err) {
        console.error('❌ Redis QR code SET error:', err);
    }
});

client.on('ready', async () => {
    console.log('✅ WhatsApp Adapter is ready and connected.');
    // Update status in Redis
    try {
        await redisClient.set('whatsapp:status', 'connected');
        await redisClient.del('whatsapp:qr_code'); // QR code is no longer needed
    } catch (err) {
        console.error('❌ Redis status SET error:', err);
    }

    // Ensure Redis is connected before starting consumer
    if (!redisClient.isOpen) {
        try {
            await connectRedis();
        } catch (err) {
            console.error('❌ Redis connection error:', err);
            return;
        }
    }

    startRedisConsumer();
});

client.on('message', async message => {
    const chat = await message.getChat();
    if (chat.isGroup) return; // Ignore group messages

    const userId = message.from;
    console.log(`💬 Received message from ${userId}`);

    try {
        let messagePayload = {
            userId: userId,
            chatId: message.from,
            timestamp: String(message.timestamp),
            agentId: 'default', // Placeholder
            body: '',
            mediaKey: '',
            mediaType: ''
        };

        if (message.hasMedia) {
            const media = await message.downloadMedia();
            if (media && media.mimetype.startsWith('audio/')) {
                console.log(`🎤 Received audio message from ${userId}. Type: ${media.mimetype}`);

                const mediaKey = `${userId}/${uuidv4()}.${media.mimetype.split('/')[1]}`;

                // Upload to R2
                await s3Client.send(new PutObjectCommand({
                    Bucket: R2_BUCKET_NAME,
                    Key: mediaKey,
                    Body: Buffer.from(media.data, 'base64'),
                    ContentType: media.mimetype,
                }));

                console.log(`☁️  Uploaded audio to R2 with key: ${mediaKey}`);

                messagePayload.mediaKey = mediaKey;
                messagePayload.mediaType = media.mimetype;

            } else {
                console.log(`📸 Media from ${userId} is not audio, ignoring.`);
                message.reply("Sorry, I can only process text and audio messages for now.");
                return;
            }
        } else {
            console.log(`✍️ Received text message from ${userId}: "${message.body}"`);
            messagePayload.body = message.body;
        }

        // Publish to Redis Stream
        await redisClient.xAdd(
            STREAM_IN,
            '*',
            messagePayload,
            { TRIM: { strategy: 'MAXLEN', strategyModifier: '~', threshold: 10000 } }
        );
        console.log(`✅ Message from ${userId} published to stream '${STREAM_IN}'.`);

        chat.sendStateTyping();

    } catch (error) {
        console.error(`❌ Error processing message for ${userId}:`, error.message);
        message.reply("I'm having trouble processing your message. Please try again later.");
    }
});


// --- Redis Consumer ---
async function startRedisConsumer() {
    console.log(`👂 Starting consumer for stream '${STREAM_OUT}'...`);
    try {
        await redisClient.xGroupCreate(STREAM_OUT, CONSUMER_GROUP, '0', { MKSTREAM: true });
    } catch (e) {
        if (e.message.includes('BUSYGROUP')) {
            console.log(`Consumer group '${CONSUMER_GROUP}' already exists.`);
        } else {
            console.error('Error creating consumer group:', e);
            return;
        }
    }

    while (true) {
        try {
            const response = await redisClient.xReadGroup(
                CONSUMER_GROUP,
                CONSUMER_NAME,
                { key: STREAM_OUT, id: '>' },
                { BLOCK: 5000, COUNT: 1 }
            );

            if (response && response.length > 0) {
                // The redis v4 library returns null on timeout or an array of streams.
                // Each stream object contains a `messages` array.
                // We access the first message of the first stream.
                const streamMessage = response[0].messages[0];
                const messageId = streamMessage.id;
                const messageData = streamMessage.message; // El payload está en la propiedad 'message'

                const { userId, body } = messageData;

                console.log(`📩 Received response for ${userId} from stream: "${body}"`);

                const chat = await client.getChatById(userId);
                if (chat) {
                    chat.clearState();
                    await client.sendMessage(userId, body);
                    console.log(`✉️ Sent response to ${userId}.`);
                } else {
                    console.error(`Could not find chat with id ${userId} to send message.`);
                }

                await redisClient.xAck(STREAM_OUT, CONSUMER_GROUP, messageId);
            }
        } catch (err) {
            console.error('Error reading from Redis stream:', err);
            await new Promise(resolve => setTimeout(resolve, 5000));
        }
    }
}

initializeClient();
