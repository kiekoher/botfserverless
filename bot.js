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
                botResponse = "Claro, te cuento sobre mis servicios. Ofrezco acompañamiento individual para duelo anticipado y posterior al fallecimiento. La sesión inicial es de 80 minutos para conocernos bien, y luego tenemos sesiones de seguimiento. ¿Te gustaría saber los precios?";
            } else {
                botResponse = "Entiendo que quieres agendar una cita. Para coordinarlo, por favor indícame qué tipo de sesión te interesa: ¿inicial, de seguimiento o un paquete?";
            }
        } else {
            botResponse = "Disculpa, no te he entendido bien. ¿Podrías explicármelo de otra manera?";
        }
        
        await sendHumanResponse(chat, botResponse);
        console.log(`✉️ Respuesta para ${userId}: "${botResponse}"`);

        // Actualizar historial y logs
        let history = conversations.get(userId) || [];
        history.push({ sender: 'Usuario', message: userQuery });
        history.push({ sender: 'Natalia', message: botResponse });
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
