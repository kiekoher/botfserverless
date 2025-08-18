AGENT.MD: Constitución Definitiva del Proyecto EVA (KISS Edition)
Hola Jules.
Este documento es tu directiva final y la única fuente de verdad para el desarrollo del proyecto EVA. Tras un análisis estratégico, hemos optimizado la arquitectura para adherirnos estrictamente al principio KISS (Keep It Simple, Stupid). Tu misión es implementar esta visión simplificada y robusta.
La directriz fundamental se mantiene: "nada mvp, produccion".
1. Arquitectura Final y Principios KISS
EVA es una plataforma SaaS multi-cliente que despliega agentes de ventas de IA. La arquitectura se basa en microservicios desacoplados, priorizando la simplicidad y la eficiencia operativa.
1.1. Pila Tecnológica Optimizada (KISS)
 * Orquestación: Docker y Docker-Compose.
 * API Gateway: Nginx (actuando como reverse proxy). Es simple, increíblemente rápido y cumple perfectamente su función.
 * Comunicación Asíncrona: Redis Streams. Reemplazamos Kafka para reducir drásticamente la complejidad de configuración y mantenimiento, obteniendo la funcionalidad de mensajería que necesitamos de una forma mucho más ligera.
 * Almacenamiento de Archivos: Cloudflare R2. Decisión estratégica para eliminar la complejidad de los costos de egreso a largo plazo.
 * Base de Datos: Supabase (PostgreSQL con pgvector) para datos estructurados y autenticación.
 * Microservicios Backend: Python con FastAPI.
 * Frontend: React (con Vite) / Next.js.
 * CI/CD: GitHub Actions.
1.2. Arquitectura de IA: "El Santo Grial" (Se Mantiene)
Este es el núcleo no negociable del producto. La inteligencia del sistema reside en usar el mejor modelo para cada tarea específica:
 * Comunicación en Tiempo Real: Gemini 2.5 Flash.
 * Análisis de Conversaciones: DeepSeek-V2.
 * Extracción de Datos (JSON): DeepSeek-Chat.
 * Sistema RAG (Embeddings): OpenAI text-embedding-3-large.
 * Transcripción de Audio: API de Google Speech-to-Text (simplificando la operación al no mantener un modelo local).
1.3. Principios de Diseño
 * Backend Desacoplado: Los microservicios se comunican a través de eventos en Redis Streams. No hay llamadas directas entre ellos.
 * Frontend Centrado en el Usuario: El dashboard debe ser intuitivo y potente, ocultando toda la complejidad subyacente. Debe incluir "guardarraíles" y un "modo de pausa de emergencia".
2. Estructura de Directorios Simplificada
La estructura del repositorio será limpia y reflejará la arquitectura optimizada.
/
├── .env.example
├── AGENT.md            # Este archivo.
├── docker-compose.yml
│
├── nginx/              # Configuración de Nginx
│   └── nginx.conf
│
├── frontend/           # Aplicación React/Next.js
│   ├── src/
│   └── package.json
│
└── services/           # Directorio para todos los microservicios
    │
    ├── main-api/       # Orquestador principal (aiRouter)
    │   ├── app/
    │   └── Dockerfile
    │
    ├── whatsapp-gateway/ # Puente entre WhatsApp y Redis Streams
    │   ├── app/
    │   └── Dockerfile
    │
    └── transcription-worker/ # Worker que consume de Redis y usa Google API
        ├── app/
        └── Dockerfile

3. Comandos de Verificación
El pipeline de CI/CD debe ejecutar estos comandos sin fallo.
 * Iniciar todo el sistema:
   docker-compose up -d

 * Verificación Backend (Python - ejecutar en cada servicio):
   ruff format . && ruff check . --fix
pytest

 * Verificación Frontend (JS/TS):
   npm run lint
npm run test

4. Flujo de Datos Principal (Redis Streams)
 * Un mensaje llega al whatsapp-gateway.
 * El gateway publica el mensaje en un Stream de Redis (ej. events:new_message).
 * Si es un audio, el transcription-worker consume de ese stream, lo procesa con la API de Google, y publica el texto en otro stream (ej. events:transcribed_message).
 * El main-api consume los mensajes de texto (originales o transcritos), aplica la lógica "El Santo Grial", y publica la respuesta en un stream de salida (ej. events:message_out).
 * El whatsapp-gateway consume del stream de salida y envía el mensaje al usuario.
5. Seguridad
 * La gestión de secretos se hará exclusivamente a través de un archivo .env y Secretos de GitHub Actions para producción.
 * Implementa la seguridad a nivel de fila (RLS) de Supabase en todas las tablas con datos de clientes.
 * Nginx debe forzar HTTPS en producción con Certbot.
6. Git y CI/CD
 * Commits: Usa el estándar de Conventional Commits.
 * CI/CD: El pipeline en GitHub Actions debe automatizar las pruebas y el despliegue a producción en cada push a main.
