# 🤖 DueloAnimalBot – RAG sensible al duelo con Gemini, Supabase y Mistral (dockerizado)

Este proyecto implementa un bot de respuesta automática sensible al duelo animal, utilizando arquitectura RAG (retrieval-augmented generation) completamente dockerizada:

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

## 🧪 Tests

Instala las dependencias y ejecuta las pruebas con:

```bash
npm install
npm test
```
