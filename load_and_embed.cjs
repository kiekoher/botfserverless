const fs = require('fs');
const path = require('path');
const axios = require('axios');
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

// Configuraciones
const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;
const GEMINI_API_KEY = process.env.GEMINI_API_KEY;

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

// === CLASIFICADOR LOCAL ===
const OLLAMA_ENDPOINT = "http://localhost:11434/api/generate";

async function classifyMessage(text) {
  const prompt = `Clasifica el siguiente mensaje de usuario en intención y entidades.\n\n` +
    `Mensaje: "${text}"\n\n` +
    `Devuelve un objeto JSON así:\n{"intent": "...", "entities": {...}}`;

  try {
    const response = await axios.post(OLLAMA_ENDPOINT, {
      model: "mistral",
      prompt: prompt,
      stream: false
    });
    const result = response.data.response;
    const start = result.indexOf("{");
    const end = result.lastIndexOf("}") + 1;
    return JSON.parse(result.slice(start, end));
  } catch (err) {
    console.error("Clasificación fallida:", err.message);
    return { intent: "unknown", entities: {} };
  }
}

// === EMBEDDING GEMINI ===
const { GoogleGenerativeAI } = require('@google/generative-ai');
const genAI = new GoogleGenerativeAI(GEMINI_API_KEY);

async function getEmbedding(text) {
  try {
    const model = genAI.getGenerativeModel({ model: 'embedding-001' });
    const result = await model.embedContent({ content: text });
    return result.embedding.values;
  } catch (err) {
    console.error("Embedding fallido:", err.message);
    return null;
  }
}

async function processJsonlFile(filePath) {
  const lines = fs.readFileSync(filePath, 'utf-8').split('\n').filter(Boolean);
  for (const line of lines) {
    try {
      const data = JSON.parse(line);
      const text = data.content || (data.messages ? data.messages.map(m => m.content).join(' ') : JSON.stringify(data));
      const classification = await classifyMessage(text);
      data.intent = classification.intent;
      data.entities = classification.entities;

      const { data: inserted, error } = await supabase.from('knowledge_base').insert({
        source_file: path.basename(filePath),
        content_type: data.type || 'generic',
        data: data
      }).select('id');

      if (error) {
        console.error("Inserción fallida:", error.message);
        continue;
      }

      const knowledge_id = inserted[0].id;
      const vector = await getEmbedding(text);
      if (vector) {
        await supabase.from('embeddings').insert({
          knowledge_id,
          embedding: vector,
          content_text: text.slice(0, 500)
        });
        console.log("✅ ID", knowledge_id);
      }

    } catch (e) {
      console.error("Error en línea:", e.message);
    }
  }
}

async function main() {
  const folder = path.join(__dirname, 'jsonl_output');
  const files = fs.readdirSync(folder).filter(f => f.endsWith('.jsonl'));
  for (const file of files) {
    console.log("➡️ Procesando:", file);
    await processJsonlFile(path.join(folder, file));
  }
}

main();
