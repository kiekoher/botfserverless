require('dotenv').config();
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const { createClient } = require('redis');

const REDIS_HOST = process.env.REDIS_HOST || 'redis';
const STREAM_IN = 'events:new_message';
const STREAM_OUT = 'events:message_out';
const CONSUMER_GROUP = 'group:whatsapp-gateway';
const CONSUMER_NAME = 'consumer:whatsapp-gateway-1';

console.log("🤖 WhatsApp Gateway Initializing...");

// Redis Client Setup
const redisClient = createClient({
    url: `redis://${REDIS_HOST}:6379`
});

redisClient.on('error', (err) => console.error('Redis Client Error', err));
redisClient.connect();

console.log("🔌 Connected to Redis.");

// Anti-ban configuration
const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            '--disable-blink-features=AutomationControlled' // Key anti-detection flag
        ],
    }
});

client.on('qr', qr => {
    console.log('📱 Scan QR code to connect:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('✅ WhatsApp Adapter is ready and connected.');
    startConsumer();
});

async function startConsumer() {
    console.log(`👂 Starting consumer for stream '${STREAM_OUT}'...`);
    try {
        await redisClient.xGroupCreate(STREAM_OUT, CONSUMER_GROUP, '0', {
            MKSTREAM: true
        });
        console.log(`Consumer group '${CONSUMER_GROUP}' created or already exists.`);
    } catch (e) {
        if (e.message.includes('BUSYGROUP')) {
            console.log(`Consumer group '${CONSUMER_GROUP}' already exists.`);
        } else {
            console.error('Error creating consumer group:', e);
            return; // Exit if we can't create the group
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
                const streamRead = response[0];
                const [messageId, messageData] = streamRead.messages[0];

                const userId = messageData.userId;
                const botResponse = messageData.body;

                console.log(`📩 Received response for ${userId} from stream: "${botResponse}"`);

                // Stop "typing..." state that was set on message receipt
                const chat = await client.getChatById(userId);
                if (chat) {
                    chat.clearState();
                    await client.sendMessage(userId, botResponse);
                    console.log(`✉️ Sent response to ${userId}.`);
                } else {
                    console.error(`Could not find chat with id ${userId} to send message.`);
                }


                // Acknowledge the message
                await redisClient.xAck(STREAM_OUT, CONSUMER_GROUP, messageId);
            }
        } catch (err) {
            console.error('Error reading from Redis stream:', err);
            // Wait a bit before retrying to avoid spamming logs on connection issues
            await new Promise(resolve => setTimeout(resolve, 5000));
        }
    }
}

client.on('message', async message => {
    const chat = await message.getChat();
    if (chat.isGroup) {
        return; // Ignore group messages for now
    }

    const userId = message.from;
    const userQuery = message.body;
    console.log(`💬 Received message from ${userId}: "${userQuery}"`);

    // We will handle media messages later
    if (message.hasMedia) {
        console.log(`📸 Message from ${userId} has media, ignoring for now.`);
        return;
    }

    try {
        // The message payload for the stream
        const messagePayload = {
            userId: userId,
            chatId: message.from, // or message.to for outgoing
            timestamp: String(message.timestamp),
            body: userQuery,
            // In a real multi-agent system, we'd look up which agent this user maps to.
            // For now, main-api will be responsible for picking an agent.
            agentId: 'default' // Placeholder
        };

        // Publish to Redis Stream
        await redisClient.xAdd(STREAM_IN, '*', messagePayload);

        console.log(`✅ Message from ${userId} published to stream '${STREAM_IN}'.`);

        // Simulate "typing..." to acknowledge receipt
        chat.sendStateTyping();

    } catch (error) {
        console.error(`❌ Error publishing message for ${userId} to Redis:`, error.message);
        // Optionally, send an error message back to the user
        await message.reply("Lo siento, estoy teniendo problemas para procesar tu mensaje. Por favor, intenta de nuevo en un momento.");
    }
});

client.initialize();
