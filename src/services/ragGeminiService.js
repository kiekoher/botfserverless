// =====================================================================
// == CEREBRO HÍBRIDO CON MEMORIA CONVERSACIONAL (CrezgoBot)           ==
// =====================================================================
import 'dotenv/config';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { supabase } from './supabaseClient.js';
import BOT_PERSONA from '../config/persona.js';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const embeddingModel = genAI.getGenerativeModel({ model: "embedding-001" });
// --- CORRECCIÓN VALIDADA ---
// Se utiliza el nombre del modelo estable para evitar errores de API.
const generationModel = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });

/**
 * Genera un embedding (vector numérico) para un texto dado.
 * @param {string} text - El texto a procesar.
 * @returns {Promise<number[]|null>} El vector de embedding o null si hay un error.
 */
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

/**
 * Procesa la consulta de un usuario utilizando el modelo RAG.
 * Busca en la base de conocimientos y genera una respuesta contextualizada.
 * @param {string} userQuery - El mensaje del usuario.
 * @param {Array<{sender: string, message: string}>} conversationHistory - El historial de la conversación actual.
 * @returns {Promise<{response: string, context: string[]}>} La respuesta del bot y el contexto utilizado.
 */
export const processRagQuery = async (userQuery, conversationHistory) => {
    const queryEmbedding = await getEmbedding(userQuery);
    if (!queryEmbedding) {
        // Respuesta por defecto si no se puede generar el embedding
        return { response: "Hola, soy tu asesor de Crezgo. ¿En qué puedo ayudarte hoy?", context: [] };
    }

    // Llama a la función de Supabase para encontrar los chunks de texto más similares
    const { data: chunks, error } = await supabase.rpc('match_documents', {
        query_embedding: queryEmbedding,
        match_threshold: 0.77, // Umbral de similitud (ajustable)
        match_count: 5 // Número máximo de chunks a recuperar
    });

    if (error) {
        console.error("Error al buscar chunks en Supabase:", error);
    }
    
    let prompt;
    let contextForLog = [];
    const historyText = conversationHistory.map(line => `**${line.sender}:** ${line.message}`).join('\n');

    if (error || !chunks || chunks.length === 0) {
        // Si no se encuentra contexto, se genera una respuesta basada solo en la persona y el historial
        prompt = `${BOT_PERSONA}\n\n### CONVERSACIÓN ACTUAL\n${historyText}\n**Usuario:** ${userQuery}\n\n### INSTRUCCIÓN\nNo se encontró información específica en los documentos. Responde al usuario basándote en el historial y tu rol de asesor de Crezgo.`;
    
    } else {
        // Si se encuentra contexto, se construye un prompt más completo
        const contextText = chunks.map(c => c.content_text).join('\n\n---\n\n');
        contextForLog = chunks.map(c => c.content_text);
        
        prompt = `${BOT_PERSONA}\n\n### CONVERSACIÓN ACTUAL\n${historyText}\n**Usuario:** ${userQuery}\n\n### INFORMACIÓN DE APOYO (Contexto Adicional)\n\`\`\`\n${contextText}\n\`\`\`\n\n### INSTRUCCIÓN\nUsando el historial y la información de apoyo, responde como asesor de Crezgo de forma cercana y profesional. Integra la información, no la cites directamente.`;
    }

    try {
        const result = await generationModel.generateContent(prompt);
        const response = result.response;
        return { response: response.text(), context: contextForLog };
    } catch (genError) {
        console.error('Error en API Generación Gemini:', genError);
        // Respuesta de emergencia en caso de fallo de la API de Gemini
        return { response: "En este momento, encuentro una dificultad para procesar tu mensaje. Te pido un momento, por favor.", context: [] };
    }
};
