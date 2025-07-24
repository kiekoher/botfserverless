// =================================================================
// ==      ORQUESTADOR PRINCIPAL EVA (TODO GEMINI)                ==
// =================================================================
import 'dotenv/config';
import pkg from 'whatsapp-web.js';
const { Client, LocalAuth } = pkg;
import qrcode from 'qrcode-terminal';
import { processRagQuery } from './src/services/ragGeminiService.js';
import { classifyAndExtract } from './src/services/geminiClassifier.js'; // <-- CAMBIO IMPORTANTE
import { sendHumanResponse } from './src/utils/humanBehavior.js';
import { getClarificationMessage } from './src/utils/helpers.js';
import { logConversation } from './src/services/supabaseClient.js';

console.log("🚀 Iniciando Orquestador EVA (Todo-Gemini)...");

const conversations = new Map();

const client = new Client({
    authStrategy: new LocalAuth(),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas', '--no-first-run', '--no-zygote',
            '--single-process', '--disable-gpu'
        ]
    }
});

client.on('qr', qr => {
    console.log('📱 Escanea este código QR para conectar el bot:');
    qrcode.generate(qr, { small: true });
});

client.on('ready', () => {
    console.log('✅ Cliente de WhatsApp conectado y listo.');
});

client.on('message', async (message) => {
    const chat = await message.getChat();
    if (chat.isGroup) return;

    const userId = message.from;
    const userQuery = message.body;
    console.log(`💬 Mensaje de ${userId}: "${userQuery}"`);

    try {
        // Usamos el nuevo clasificador de Gemini
        const classification = await classifyAndExtract(userQuery);
        let botResponse;
        let contextChunks = [];

        if (classification.decision === 'use_rag') {
            const history = conversations.get(userId) || [];
            const ragResult = await processRagQuery(classification.summary_for_rag, history);
            botResponse = ragResult.response;
            contextChunks = ragResult.context;
        } else if (classification.decision === 'use_tool') {
            // Lógica de herramientas (simplificada por ahora)
            if (classification.tool_call.name === 'get_service_info') {
                botResponse = "Con gusto, te cuento sobre los servicios de Crezgo: estrategia empresarial, finanzas, marketing digital y outsourcing financiero. ¿Hay algún área específica que quieras fortalecer?";
            } else {
                botResponse = "Perfecto, puedo ayudarte a agendar una llamada de diagnóstico. ¿Qué día y hora te convienen para que uno de nuestros asesores te contacte?";
            }
        } else {
            botResponse = getClarificationMessage();
        }
        
        await sendHumanResponse(chat, botResponse);
        console.log(`✉️ Respuesta para ${userId}: "${botResponse}"`);

        // Actualizar historial y logs
        let history = conversations.get(userId) || [];
        history.push({ sender: 'Usuario', message: userQuery });
        history.push({ sender: 'CrezgoBot', message: botResponse });
        conversations.set(userId, history.slice(-20));
        
        await logConversation(
            userId,
            userQuery,
            botResponse,
            contextChunks
        );

    } catch (error) {
        console.error(`❌ Error fatal procesando el mensaje de ${userId}:`, error);
        await chat.sendMessage("Lo siento, ocurrió un error inesperado en mi sistema. Ya estoy trabajando para solucionarlo.");
    }
});

client.initialize();
