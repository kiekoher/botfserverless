// =====================================================================
// == CEREBRO HÍBRIDO CON MEMORIA CONVERSACIONAL (Personalidad Natalia) ==
// =====================================================================
import 'dotenv/config';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { supabase } from './supabaseClient.js';
import BOT_PERSONA_NATALIA from '../config/persona.js';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const embeddingModel = genAI.getGenerativeModel({ model: "embedding-001" });
const generationModel = genAI.getGenerativeModel({ model: "gemini-1.5-flash-latest" });

export const getEmbedding = async (text) => {
    if (!text || text.trim() === '') return null;
    try {
        const result = await embeddingModel.embedContent(text);
        return result.embedding.values;
    } catch (error) {
        console.error('Error en API Embeddings Gemini:', error);
        return null;
    }
};

export const processRagQuery = async (userQuery, conversationHistory) => {
    const queryEmbedding = await getEmbedding(userQuery);
    if (!queryEmbedding) {
        return { response: "Hola, soy Natalia Jaller. Te doy la bienvenida a este espacio seguro. Estoy aquí para escucharte.", context: [] };
    }

    const { data: chunks, error } = await supabase.rpc('match_chunks', {
        query_embedding: queryEmbedding,
        match_threshold: 0.77,
        match_count: 5
    });

    if (error) {
        console.error("Error al buscar chunks en Supabase:", error);
    }
    
    let prompt;
    let contextForLog = [];
    const historyText = conversationHistory.map(line => `**${line.sender}:** ${line.message}`).join('\n');

    if (error || !chunks || chunks.length === 0) {
        prompt = `${BOT_PERSONA_NATALIA}\n\n### CONVERSACIÓN ACTUAL\n${historyText}\n**Usuario:** ${userQuery}\n\n### INSTRUCCIÓN\nNo se encontró información específica en los documentos. Responde al usuario basándote en el historial y tu rol como Natalia. Continúa la conversación de forma empática y orientadora.`;
    
    } else {
        const contextText = chunks.map(c => c.chunk_text).join('\n\n---\n\n');
        contextForLog = chunks.map(c => c.chunk_text);
        
        prompt = `${BOT_PERSONA_NATALIA}\n\n### CONVERSACIÓN ACTUAL\n${historyText}\n**Usuario:** ${userQuery}\n\n### INFORMACIÓN DE APOYO (Contexto Adicional)\n\`\`\`\n${contextText}\n\`\`\`\n\n### INSTRUCCIÓN\nUsando el historial y la información de apoyo, responde como Natalia de forma cálida, profesional y natural. Integra la información, no la cites.`;
    }

    try {
        const result = await generationModel.generateContent(prompt);
        const response = result.response;
        return { response: response.text(), context: contextForLog };
    } catch (genError) {
        console.error('Error en API Generación Gemini:', genError);
        return { response: "En este momento, encuentro una dificultad para procesar tu mensaje. Te pido un momento, por favor.", context: [] };
    }
};
