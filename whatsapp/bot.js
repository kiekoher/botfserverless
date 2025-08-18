require('dotenv').config();
const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const axios = require('axios');

const BACKEND_URL = process.env.BACKEND_URL || 'http://nginx/api/chat';

console.log("🤖 WhatsApp Adapter Initializing...");

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
});

// Simple in-memory conversation history
const conversationHistory = new Map();

client.on('message', async message => {
    const chat = await message.getChat();
    if (chat.isGroup) {
        return; // Ignore group messages
    }

    const userId = message.from;
    const userQuery = message.body;
    console.log(`💬 Received message from ${userId}: "${userQuery}"`);

    try {
        // Simulate "typing..."
        chat.sendStateTyping();

        // Human-like delay
        const randomDelay = Math.floor(Math.random() * (3000 - 1000 + 1) + 1000); // 1-3 seconds
        await new Promise(resolve => setTimeout(resolve, randomDelay));

        const history = conversationHistory.get(userId) || [];

        const response = await axios.post(BACKEND_URL, {
            user_id: userId,
            query: userQuery,
            conversation_history: history
        });

        const botResponse = response.data.response;

        // Stop "typing..."
        chat.clearState();

        await message.reply(botResponse);
        console.log(`✉️ Sent response to ${userId}: "${bot_response}"`);

        // Update history
        history.push({ role: 'user', content: userQuery });
        history.push({ role: 'assistant', content: botResponse });
        conversationHistory.set(userId, history.slice(-20)); // Keep last 10 turns

    } catch (error) {
        chat.clearState();
        console.error(`❌ Error processing message for ${userId}:`, error.message);
        if (error.response) {
            console.error('Backend Error:', error.response.data);
        }
        await message.reply("Lo siento, estoy teniendo problemas para conectarme con mi cerebro. Por favor, intenta de nuevo en un momento.");
    }
});

client.initialize();
