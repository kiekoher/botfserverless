const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(__dirname, 'jsonl_output');

function validateJSONL(filePath) {
  const lines = fs.readFileSync(filePath, 'utf-8').split('\n').filter(Boolean);
  let valid = true;
  lines.forEach((line, index) => {
    try {
      JSON.parse(line);
    } catch (e) {
      console.error(`❌ Línea inválida en ${filePath}, línea ${index + 1}:`, e.message);
      valid = false;
    }
  });
  if (valid) console.log("✅ JSONL válido:", path.basename(filePath));
  return valid;
}

function main() {
  const files = fs.readdirSync(OUTPUT_DIR).filter(f => f.endsWith('.jsonl'));
  for (const file of files) {
    validateJSONL(path.join(OUTPUT_DIR, file));
  }
}

main();
