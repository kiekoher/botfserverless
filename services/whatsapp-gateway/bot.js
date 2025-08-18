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

// Redis Client
const redisClient = createClient({ url: `redis://${REDIS_HOST}:6379` });
redisClient.on('error', (err) => console.error('Redis Client Error', err));
redisClient.connect();
console.log("🔌 Connected to Redis.");

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
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
    }
});

// --- Event Handlers ---
client.on('qr', qr => {
    console.log('📱 Scan QR code to connect:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('✅ WhatsApp Adapter is ready and connected.');
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
        await redisClient.xAdd(STREAM_IN, '*', messagePayload);
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
                const [messageId, messageData] = response[0].messages[0];
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

client.initialize();
