const fs = require('fs');
const path = require('path');

const INPUT_DIR = path.join(__dirname, 'documentos');
const OUTPUT_DIR = path.join(__dirname, 'jsonl_output');

if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR);

function convertTextFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8').trim();
  const lines = content.split(/\n{2,}/).map(p => p.trim()).filter(Boolean);

  const jsonl = lines.map(line => JSON.stringify({ content: line })).join('\n');
  const outputFile = path.join(OUTPUT_DIR, path.basename(filePath) + '.jsonl');

  fs.writeFileSync(outputFile, jsonl, 'utf-8');
  console.log("✅ Generado:", outputFile);
}

function main() {
  const files = fs.readdirSync(INPUT_DIR).filter(f => f.endsWith('.txt'));
  for (const file of files) {
    convertTextFile(path.join(INPUT_DIR, file));
  }
}

main();
