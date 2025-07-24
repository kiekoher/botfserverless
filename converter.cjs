// converter.cjs

/**
 * -----------------------------------------------------------------------------
 * Script de Conversión de Documentos a JSONL
 * -----------------------------------------------------------------------------
 * Este script toma un archivo de entrada (PDF, DOCX, TXT) y lo convierte
 * a un archivo de formato JSONL (JSON Lines). Cada línea del archivo de salida
 * es un objeto JSON que contiene el texto extraído del documento.
 *
 * Uso desde la línea de comandos:
 * node converter.cjs <ruta_del_archivo_de_entrada> <ruta_del_archivo_de_salida.jsonl>
 *
 * Dependencias:
 * - pdf-parse: Para extraer texto de archivos PDF.
 * - mammoth: Para extraer texto de archivos DOCX.
 * - fs/promises: Para operaciones de archivo asíncronas.
 * - path: Para manejar rutas de archivos.
 * -----------------------------------------------------------------------------
 */

// Importación de módulos necesarios
const fs = require('fs/promises'); // Módulo de sistema de archivos para operaciones asíncronas
const path = require('path'); // Módulo para manejar y transformar rutas de archivos
const pdf = require('pdf-parse'); // Librería para parsear archivos PDF
const mammoth = require('mammoth'); // Librería para extraer texto de DOCX

/**
 * Función principal que orquesta la conversión del archivo.
 * @param {string} inputPath - La ruta al archivo de entrada.
 * @param {string} outputPath - La ruta donde se guardará el archivo .jsonl de salida.
 */
async function convertFileToJsonl(inputPath, outputPath) {
  try {
    // Valida que las rutas de entrada y salida han sido proporcionadas.
    if (!inputPath || !outputPath) {
      throw new Error('Se requieren las rutas de los archivos de entrada y salida.');
    }

    // Asegura que el directorio de salida exista
    await fs.mkdir(path.dirname(outputPath), { recursive: true });

    // Obtiene la extensión del archivo para determinar cómo procesarlo.
    const extension = path.extname(inputPath).toLowerCase();
    let textContent; // Variable para almacenar el texto extraído.

    // Lee el contenido del archivo de entrada en un buffer.
    const dataBuffer = await fs.readFile(inputPath);

    // Selección del método de extracción basado en la extensión del archivo.
    switch (extension) {
      case '.pdf':
        // Si es un PDF, usa pdf-parse para extraer el texto.
        console.log(`📄 Procesando archivo PDF: ${inputPath}`);
        const pdfData = await pdf(dataBuffer);
        textContent = pdfData.text;
        break;

      case '.docx':
        // Si es un DOCX, usa mammoth para extraer el texto plano.
        console.log(`📄 Procesando archivo DOCX: ${inputPath}`);
        const docxResult = await mammoth.extractRawText({ buffer: dataBuffer });
        textContent = docxResult.value;
        break;

      case '.txt':
        // Si es un TXT, simplemente decodifica el buffer a texto.
        console.log(`📄 Procesando archivo de texto: ${inputPath}`);
        textContent = dataBuffer.toString('utf8');
        break;

      default:
        // Si el formato no es soportado, lanza un error.
        throw new Error(`Formato de archivo no soportado: ${extension}`);
    }

    // Prepara el contenido para el formato JSONL.
    // Se eliminan saltos de línea excesivos y se escapa el contenido para ser un string JSON válido.
    const cleanedText = textContent.replace(/\s+/g, ' ').trim();
    const jsonlContent = JSON.stringify({ text: cleanedText });

    // Escribe el objeto JSON como una línea en el archivo de salida.
    await fs.writeFile(outputPath, jsonlContent + '\n');

    console.log(`✅ Conversión exitosa. Archivo guardado en: ${outputPath}`);
  } catch (error) {
    // Manejo de errores: imprime el error en la consola y sale del proceso con un código de error.
    console.error('❌ Error durante la conversión del archivo:', error.message);
    process.exit(1); // Termina el script con un estado de fallo.
  }
}

// --- Ejecución del Script ---
// El script se ejecuta solo si se llama directamente desde la línea de comandos.
if (require.main === module) {
  // Obtiene las rutas de los archivos desde los argumentos de la línea de comandos.
  const inputFile = process.argv[2]; // El primer argumento es la ruta de entrada.
  const outputFile = process.argv[3]; // El segundo argumento es la ruta de salida.

  // Llama a la función principal para iniciar la conversión.
  convertFileToJsonl(inputFile, outputFile);
}

// Exporta la función para que pueda ser utilizada por otros módulos (como auto_ingest.cjs).
module.exports = { convertFileToJsonl };
