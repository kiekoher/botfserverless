const axios = require('axios');
const fs = require('fs');
const path = require('path');

const OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"; // Ollama API

async function classifyMessageOllama(text) {
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
  } catch (e) {
    console.error("❌ Error:", e.message);
    return { intent: "unknown", entities: {} };
  }
}

async function processJsonl(filePath) {
  const lines = fs.readFileSync(filePath, 'utf-8').split('\n').filter(Boolean);
  const output = [];

  for (const line of lines) {
    const obj = JSON.parse(line);
    const base = obj.content || (obj.messages ? obj.messages.map(m => m.content).join(" ") : "");
    const result = await classifyMessageOllama(base);
    obj.intent = result.intent;
    obj.entities = result.entities;
    output.push(JSON.stringify(obj));
  }

  const outFile = path.join(path.dirname(filePath), 'tagged_' + path.basename(filePath));
  fs.writeFileSync(outFile, output.join('\n'), 'utf-8');
  console.log("✅ Archivo generado:", outFile);
}

if (require.main === module) {
  const input = process.argv[2];
  if (!input) {
    console.log("Uso: node classify_with_ollama.js <archivo.jsonl>");
    process.exit(1);
  }
  processJsonl(input);
}
