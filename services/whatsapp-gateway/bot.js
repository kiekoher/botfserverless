require('dotenv').config();
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');
const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { v4: uuidv4 } = require('uuid');
const http = require('http');
const clientMetrics = require('prom-client');
const pino = require('pino');
const logger = pino();
clientMetrics.collectDefaultMetrics();
const sessionGauge = new clientMetrics.Gauge({
    name: 'eva_whatsapp_session_connected',
    help: 'WhatsApp session connection status (1 connected, 0 disconnected)'
});

// --- Configuration ---
const MAIN_API_URL = process.env.MAIN_API_URL;
const USER_ID = process.env.WHATSAPP_USER_ID;

if (!USER_ID) {
    logger.error('❌ WHATSAPP_USER_ID environment variable is required.');
    process.exit(1);
}
if (!MAIN_API_URL) {
    logger.error('❌ MAIN_API_URL environment variable is required.');
    process.exit(1);
}

// R2 Configuration
const R2_ENDPOINT_URL = process.env.R2_ENDPOINT_URL;
const R2_BUCKET_NAME = process.env.R2_BUCKET_NAME;
const R2_ACCESS_KEY_ID = process.env.R2_ACCESS_KEY_ID;
const R2_SECRET_ACCESS_KEY = process.env.R2_SECRET_ACCESS_KEY;
const R2_REGION = process.env.R2_REGION || "auto";

if (!R2_ENDPOINT_URL || !R2_BUCKET_NAME || !R2_ACCESS_KEY_ID || !R2_SECRET_ACCESS_KEY) {
    logger.error('❌ Missing R2 configuration. Set R2_ENDPOINT_URL, R2_BUCKET_NAME, R2_ACCESS_KEY_ID, and R2_SECRET_ACCESS_KEY.');
    process.exit(1);
}
const MAX_AUDIO_BYTES = 10 * 1024 * 1024;

// --- Initialize Clients ---
logger.info("🤖 WhatsApp Gateway Initializing...");

// S3 Client for R2
const s3Client = new S3Client({
    endpoint: R2_ENDPOINT_URL,
    region: R2_REGION,
    credentials: {
        accessKeyId: R2_ACCESS_KEY_ID,
        secretAccessKey: R2_SECRET_ACCESS_KEY,
    },
});
logger.info("☁️  R2 S3 Client Initialized.");

// Health and Metrics server
const metricsServer = http.createServer(async (req, res) => {
    if (req.url === '/metrics') {
        res.setHeader('Content-Type', clientMetrics.register.contentType);
        res.end(await clientMetrics.register.metrics());
    } else if (req.url === '/health') {
        try {
            const state = await client.getState();
            if (state === 'CONNECTED') {
                res.statusCode = 200;
                res.setHeader('Content-Type', 'application/json');
                res.end(JSON.stringify({ status: 'ok', state: state }));
            } else {
                logger.warn(`Healthcheck failed: client state is ${state}`);
                res.statusCode = 503;
                res.setHeader('Content-Type', 'application/json');
                res.end(JSON.stringify({ status: 'error', state: state }));
            }
        } catch (e) {
            logger.error('Healthcheck failed with error:', e.message);
            res.statusCode = 500;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({ status: 'error', message: e.message }));
        }
    } else {
        res.statusCode = 404;
        res.end();
    }
});
if (process.env.NODE_ENV !== 'test') {
    metricsServer.listen(9100, () => logger.info('📊 Metrics server running on :9100/metrics'));
}

// WhatsApp Client
const SESSION_PATH = process.env.WHATSAPP_SESSION_PATH || '/app/session';
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
        logger.error('❌ WhatsApp init error:', err);
        await new Promise((res) => setTimeout(res, delay));
        return initializeClient(retry + 1);
    }
}

client.on('disconnected', async (reason) => {
    logger.error(`⚠️ WhatsApp disconnected: ${reason}. Reinitializing...`);
    sessionGauge.set(0);
    await initializeClient();
});

// --- Event Handlers ---
client.on('qr', (qr) => {
    logger.info('📱 Scan QR code to connect:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    logger.info('✅ WhatsApp Adapter is ready and connected.');
    sessionGauge.set(1);
});

client.on('message', async message => {
    const chat = await message.getChat();
    if (chat.isGroup) return; // Ignore group messages

    const contact = await message.getContact();
    const userName = contact.pushname || contact.name || message.from;

    logger.info(`💬 Received message from ${userName} (${message.from})`);

    try {
        let messagePayload = {
            userId: message.from,
            userName: userName,
            chatId: message.from,
            timestamp: String(message.timestamp),
            agentId: 'default', // Placeholder, API should determine the agent
            body: '',
            mediaKey: '',
            mediaType: ''
        };

        if (message.hasMedia) {
            const media = await message.downloadMedia();
            if (media && media.mimetype.startsWith('audio/')) {
                const audioBuffer = Buffer.from(media.data, 'base64');
                if (audioBuffer.length > MAX_AUDIO_BYTES) {
                    logger.error(`Audio from ${message.from} exceeds size limit.`);
                    message.reply('Audio file is too large. Max 10MB.');
                    return;
                }
                logger.info(`🎤 Received audio message from ${message.from}. Type: ${media.mimetype}`);
                const mediaKey = `${message.from}/${uuidv4()}.${media.mimetype.split('/')[1]}`;
                await s3Client.send(new PutObjectCommand({
                    Bucket: R2_BUCKET_NAME,
                    Key: mediaKey,
                    Body: audioBuffer,
                    ContentType: media.mimetype,
                }));
                logger.info(`☁️  Uploaded audio to R2 with key: ${mediaKey}`);
                messagePayload.mediaKey = mediaKey;
                messagePayload.mediaType = media.mimetype;
            } else {
                logger.info(`📸 Media from ${message.from} is not audio, ignoring.`);
                message.reply('Sorry, I can only process text and audio messages for now.');
                return;
            }

        } else {
            logger.info(`✍️ Received text message from ${message.from}: "${message.body}"`);
            messagePayload.body = message.body;
        }

        // Forward to Main API via HTTP POST
        logger.info(`➡️ Forwarding message from ${message.from} to API...`);
        await axios.post(MAIN_API_URL, messagePayload, {
            headers: { 'Content-Type': 'application/json' }
        });
        logger.info(`✅ Message from ${message.from} successfully forwarded to API.`);

        chat.sendStateTyping();

    } catch (error) {
        logger.error(`❌ Error processing message for ${message.from}:`, error.message);
        if (error.response) {
            logger.error(`API Response Error: ${error.response.status} ${JSON.stringify(error.response.data)}`);
        }
        message.reply("I'm having trouble processing your message. Please try again later.");
    }
});

if (process.env.NODE_ENV !== 'test') {
    initializeClient();
}

module.exports = { client };
