const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const DOCUMENTS_DIR = '/app/documentos';
const INTERVAL_MS = 5000;

console.log(`👀 Observando carpeta: ${DOCUMENTS_DIR}`);

let processedFiles = new Set();

const isTextFile = (filename) => {
  return filename.endsWith('.txt');
};

const runScript = (script, args = []) => {
  return new Promise((resolve, reject) => {
    const proc = spawn('node', [script, ...args], {
      stdio: 'inherit',
      cwd: '/app',
    });

    proc.on('close', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${script} finalizó con código ${code}`));
    });
  });
};

const processFile = async (filename) => {
  if (processedFiles.has(filename)) return;

  const filepath = path.join(DOCUMENTS_DIR, filename);
  if (!fs.existsSync(filepath)) return;

  try {
    console.log(`📄 Detectado nuevo archivo: ${filename}`);
    console.log(`🔁 Ejecutando conversión...`);
    await runScript('converter.cjs', [filepath]);

    console.log(`✅ Validando JSONL...`);
    await runScript('validate_jsonl.cjs');

    console.log(`📥 Ejecutando load_and_embed...`);
    await runScript('load_and_embed.cjs');

    processedFiles.add(filename);
    console.log(`🎉 Procesado con éxito: ${filename}`);
  } catch (err) {
    console.error(`❌ Error en procesamiento automático:`, err.message);
  }
};

const pollDirectory = () => {
  fs.readdir(DOCUMENTS_DIR, (err, files) => {
    if (err) {
      console.error(`❌ Error leyendo directorio: ${err.message}`);
      return;
    }

    files.filter(isTextFile).forEach(processFile);
  });
};

setInterval(pollDirectory, INTERVAL_MS);
