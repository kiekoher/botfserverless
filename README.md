# 🤖 CrezgoBot – Chatbot para pymes con RAG usando Gemini y Supabase (dockerizado)

Este proyecto implementa un bot de atención al cliente y ventas para la firma de consultoría **Crezgo**. Se basa en una arquitectura RAG (retrieval-augmented generation) completamente dockerizada:

- 📁 Ingesta automática de documentos desde `/documentos`
- 📄 Conversión y validación `.txt` ➜ `.jsonl`
- 🧠 Clasificación con modelo local Mistral 7B Instruct (vía Ollama)
- 🧩 Inserción y embeddings en Supabase
- 💬 Generación de respuestas contextualizadas con Gemini

---

## 🚀 Instalación automática en VPS

1. Instala Docker y Docker Compose:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose
```

## 📄 Variables de entorno

1. Copia el archivo `.env.example` a `.env`.
2. Completa los valores requeridos:

   - `GEMINI_API_KEY`: clave de API para Gemini.
   - `SUPABASE_URL` y `SUPABASE_KEY`: credenciales de tu proyecto Supabase.
   - `SUPABASE_SERVICE_KEY`: clave de servicio para ingestión.

## 🧪 Tests

Instala las dependencias y ejecuta las pruebas con:

```bash
npm install
npm test
```

## ❗ Limpieza de contenedores antiguos

Si al ejecutar `docker compose up` ves nombres de contenedores
relacionados con proyectos anteriores (por ejemplo `dueloanimalbot_bot`),
es probable que existan contenedores residuales en tu sistema.
Detén y elimina los servicios previos antes de volver a construir:

```bash
docker compose down
docker compose up --build -d
```

Esto asegurará que se utilicen los nombres de contenedor definidos en
`docker-compose.yml` (como `eva_bot` y `eva_ingest`).
