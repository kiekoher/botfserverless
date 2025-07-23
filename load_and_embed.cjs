const fs = require('fs');
const path = require('path');
const { createClient } = require('@supabase/supabase-js');
const { GoogleGenerativeAI } = require('@google/generative-ai');
require('dotenv').config();

// === CONFIGURACIONES ===
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY || !GEMINI_API_KEY) {
    console.error("❌ Error: Faltan variables de entorno. Revisa tu archivo .env.");
    process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

// === CLASIFICADOR CON GEMINI ===
async function classifyMessageWithGemini(text) {
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" });
    const prompt = `
    Clasifica el siguiente texto de la base de conocimiento de una psicóloga experta en duelo animal.
    Identifica la intención y extrae entidades.
    Texto: "${text}"
    Devuelve solo un objeto JSON: {"intent": "...", "entities": {...}}.
    `;
    try {
        const result = await model.generateContent(prompt);
        const responseText = result.response.text();
        const jsonMatch = responseText.match(/\{[\s\S]*\}/);
        if (jsonMatch) return JSON.parse(jsonMatch[0]);
        return { intent: "desconocido", entities: {} };
    } catch (err) {
        console.error("Error en API de clasificación Gemini:", err);
        return { intent: "desconocido", entities: {} };
    }
}

// === EMBEDDING CON GEMINI (CON VALIDACIÓN) ===
async function getEmbedding(text) {
    // ---- MEJORA CLAVE: Validación para no enviar texto vacío ----
    if (!text || text.trim() === '') {
        console.warn("Saltando embedding para texto vacío.");
        return null;
    }
    // -----------------------------------------------------------
    try {
        const model = genAI.getGenerativeModel({ model: 'embedding-001' });
        const result = await model.embedContent(text);
        return result.embedding.values;
    } catch (err) {
        console.error("Error en API de Embedding Gemini:", err);
        return null;
    }
}

// === PROCESAMIENTO PRINCIPAL ===
async function processJsonlFile(filePath) {
    const lines = fs.readFileSync(filePath, 'utf-8').split('\n').filter(Boolean);

    for (const line of lines) {
        try {
            const data = JSON.parse(line);
            const text = data.content || '';

            // Solo procesamos si hay texto
            if (text && text.trim() !== '') {
                const classification = await classifyMessageWithGemini(text);
                data.intent = classification.intent;
                data.entities = classification.entities;

                const { data: inserted, error: insertError } = await supabase.from('knowledge_base').insert({
                    source_file: path.basename(filePath),
                    content_type: 'generic',
                    data: data
                }).select('id').single();

                if (insertError) {
                    console.error(`Error insertando en knowledge_base:`, insertError);
                    continue;
                }

                const knowledge_id = inserted.id;
                const vector = await getEmbedding(text);

                if (vector) {
                    const { error: embedError } = await supabase.from('embeddings').insert({
                        knowledge_id,
                        embedding: vector,
                        content_text: text.slice(0, 1000)
                    });
                    if (embedError) {
                        console.error(`Error insertando embedding:`, embedError);
                    } else {
                        console.log(`✅ Procesado y guardado en Supabase. ID: ${knowledge_id}`);
                    }
                }
            }
        } catch (e) {
            console.error(`Error fatal procesando línea del archivo ${path.basename(filePath)}:`, e);
        }
    }
}

async function main() {
    console.log("🚀 Iniciando proceso de carga y embedding (versión robusta)...");
    const folder = path.join(__dirname, 'jsonl_output');
    if (!fs.existsSync(folder)) return;
    
    const files = fs.readdirSync(folder).filter(f => f.endsWith('.jsonl'));
    if (files.length === 0) return;

    for (const file of files) {
        console.log(`➡️  Procesando archivo: ${file}`);
        await processJsonlFile(path.join(folder, file));
    }
    console.log("🎉 Proceso de carga y embedding finalizado.");
}

if (require.main === module) {
    main();
}
