// =================================================================
// ==              AGENTE CONVERSACIONAL - BOT.JS                 ==
// =================================================================
import 'dotenv/config';
import { Client, LocalAuth } from 'whatsapp-web.js';
import qrcode from 'qrcode-terminal';
import { processRagQuery } from './src/services/ragGeminiService.js';
import { sendHumanResponse } from './src/utils/humanBehavior.js';
import { logConversation } from './src/services/supabaseClient.js';

console.log('🚀 Iniciando Agente Conversacional DueloAnimalBot...');

const client = new Client({
    authStrategy: new LocalAuth(), // Guarda la sesión para no escanear el QR cada vez
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-gpu'
        ],
    }
});

// Evento para mostrar el QR en la terminal del contenedor
client.on('qr', (qr) => {
    console.log('📱 Escanea este código QR con el WhatsApp que usará el bot.');
    console.log('📌 Para ver el QR, ejecuta: sudo docker compose logs bot');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('✅ ¡El bot de WhatsApp está conectado y listo para conversar!');
});

client.on('message', async (message) => {
    const chat = await message.getChat();
    if (chat.isGroup) return; // Ignorar mensajes de grupos

    const userQuery = message.body;
    console.log(`💬 Mensaje recibido de ${message.from}: "${userQuery}"`);

    try {
        const conversationHistory = []; // Simplificado
        const { response: botResponse, context } = await processRagQuery(userQuery, conversationHistory);
        await sendHumanResponse(chat, botResponse);
        console.log(`✉️ Respuesta enviada a ${message.from}: "${botResponse}"`);
        await logConversation(message.from, userQuery, botResponse, context);
    } catch (error) {
        console.error('❌ Error procesando el mensaje:', error);
        await chat.sendMessage('Lo siento, estoy teniendo dificultades para procesar tu mensaje. Inténtalo de nuevo más tarde.');
    }
});

client.initialize();
