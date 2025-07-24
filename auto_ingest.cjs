const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
require('dotenv').config();

const DOCUMENTS_DIR = process.env.INGEST_DIR || '/app/documentos';
const INTERVAL_MS = parseInt(process.env.INGEST_INTERVAL_MS, 10) || 5000;

console.log(`👀 Observando carpeta: ${DOCUMENTS_DIR}`);

let processedFiles = new Set();

const isSupportedFile = (filename) => {
  const ext = path.extname(filename).toLowerCase();
  return ['.txt', '.pdf', '.docx'].includes(ext);
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
  const outputPath = path.join('/app/jsonl_output',
    path.parse(filename).name + '.jsonl');

  try {
    console.log(`📄 Detectado nuevo archivo: ${filename}`);
    console.log(`🔁 Ejecutando conversión...`);
    await runScript('converter.cjs', [filepath, outputPath]);

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

    files.filter(isSupportedFile).forEach(processFile);
  });
};

setInterval(pollDirectory, INTERVAL_MS);
