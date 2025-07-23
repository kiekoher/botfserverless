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
    console.error("❌ Error: Faltan variables de entorno. Asegúrate de que SUPABASE_URL, SUPABASE_SERVICE_KEY y GEMINI_API_KEY estén en tu archivo .env.");
    process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

// === CLASIFICADOR CON GEMINI (CORREGIDO) ===
async function classifyMessageWithGemini(text) {
    // CORRECCIÓN: Usamos 'gemini-1.5-flash' en lugar de 'gemini-1.5-flash-latest'
    const model = genAI.getGenerativeModel({ model: "gemini-1.5-flash" }); 
    const prompt = `
    Clasifica el siguiente texto, que proviene de la base de conocimiento de una psicóloga experta en duelo animal.
    Identifica la intención principal y extrae entidades clave.
    
    Texto a analizar: "${text}"
    
    Devuelve estrictamente un objeto JSON con la estructura: {"intent": "...", "entities": {"key": "value"}}.
    Ejemplos de intención: "descripcion_servicio", "testimonio_cliente", "informacion_contacto", "precios", "metodologia_trabajo".
    `;

    try {
        const result = await model.generateContent(prompt);
        const responseText = result.response.text();
        
        const jsonMatch = responseText.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
            return JSON.parse(jsonMatch[0]);
        }
        console.error("Clasificación fallida: La respuesta de Gemini no contenía un JSON válido. Respuesta recibida:", responseText);
        return { intent: "desconocido", entities: {} };

    } catch (err) {
        console.error("Error en la API de clasificación de Gemini:", err);
        return { intent: "desconocido", entities: {} };
    }
}

// === EMBEDDING CON GEMINI ===
async function getEmbedding(text) {
    if (!text || text.trim() === '') return null;
    try {
        const model = genAI.getGenerativeModel({ model: 'embedding-001' });
        const result = await model.embedContent({ content: text });
        return result.embedding.values;
    } catch (err) {
        console.error("Error en la API de Embedding de Gemini:", err);
        return null;
    }
}

// === PROCESAMIENTO PRINCIPAL DE ARCHIVOS JSONL ===
async function processJsonlFile(filePath) {
    const lines = fs.readFileSync(filePath, 'utf-8').split('\n').filter(Boolean);

    for (const line of lines) {
        try {
            const data = JSON.parse(line);
            const text = data.content || (data.messages ? data.messages.map(m => m.content).join(' ') : JSON.stringify(data));
            
            const classification = await classifyMessageWithGemini(text);
            data.intent = classification.intent;
            data.entities = classification.entities;

            const { data: inserted, error: insertError } = await supabase.from('knowledge_base').insert({
                source_file: path.basename(filePath),
                content_type: 'generic',
                data: data
            }).select('id').single();

            if (insertError) {
                // Logueamos el error completo para más detalles
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

        } catch (e) {
            console.error(`Error fatal procesando una línea del archivo ${path.basename(filePath)}:`, e);
        }
    }
}

async function main() {
    console.log("🚀 Iniciando proceso de carga y embedding (versión corregida)...");
    const folder = path.join(__dirname, 'jsonl_output');
    
    if (!fs.existsSync(folder)) {
        console.log(`📂 El directorio ${folder} no existe. Se procesarán archivos cuando aparezcan.`);
        return;
    }
    
    const files = fs.readdirSync(folder).filter(f => f.endsWith('.jsonl'));
    if (files.length === 0) {
        console.log("No se encontraron archivos .jsonl para procesar.");
        return;
    }

    for (const file of files) {
        console.log(`➡️  Procesando archivo: ${file}`);
        await processJsonlFile(path.join(folder, file));
    }
    console.log("🎉 Proceso de carga y embedding finalizado.");
}

if (require.main === module) {
    main();
}
