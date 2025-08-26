AGENTS.md.
Markdown

# Guía para Agentes de IA (Arquitectura Serverless de Producción)

Este repositorio está preparado para colaborar con agentes de codificación. Lee este archivo antes de hacer cambios para entender la arquitectura, comandos y normas del proyecto.

## 1. Descripción general del proyecto

EVA es una plataforma SaaS multi‑tenant para desplegar agentes de ventas impulsados por IA. Sigue una **arquitectura serverless híbrida** para máxima escalabilidad y mínimo mantenimiento, con un componente clave auto-alojado.

**Servicios principales:**

* **Frontend**: Panel de control en Next.js, desplegado en **Vercel**.
* **API**: Lógica de negocio principal en Python/FastAPI, ejecutándose como **Vercel Serverless Functions**.
* **Worker de Transcripción**: Un **Cloudflare Worker** que orquesta la transcripción de audios usando la **API de Google Speech-to-Text**.
* **Worker de Embeddings**: Un **Cloudflare Worker** que genera embeddings de texto para el sistema RAG.
* **Base de Datos y Autenticación**: **Supabase Cloud** (PostgreSQL).
* **Almacenamiento de Archivos**: **Cloudflare R2** para audios y documentos.
* **Cola de Mensajes**: **Cloudflare Queues** para la comunicación asíncrona entre la API y los Workers.
* **Gateway de WhatsApp**: Un servicio Node.js que corre en un **contenedor Docker auto-alojado** en un servidor Ubuntu para mantener una sesión persistente de WhatsApp.

## 2. Estructura del repositorio

frontend/                  # Aplicación Next.js (desplegada en Vercel)
api/                       # Funciones Serverless de Python/FastAPI (desplegadas con Vercel)
workers/                   # Workers de TypeScript (desplegados en Cloudflare)
transcription-worker/    # Orquesta la transcripción con la API de Google
embedding-worker/
services/
whatsapp-gateway/        # Contenedor para el servidor Ubuntu
supabase/                  # Migraciones de base de datos
checklist.md               # Checklist de despliegue a producción


## 3. Comandos de desarrollo y pruebas

El desarrollo local se gestiona con las herramientas CLI de cada plataforma.

```bash
# Iniciar el entorno de desarrollo local de Vercel (frontend + API)
# Desde el directorio raíz
vercel dev

# Iniciar el entorno de desarrollo de Cloudflare Workers
# Desde el directorio workers/
npx wrangler dev

# Pruebas de la API (Python)
# Desde el directorio api/
pytest

4. Despliegue a Producción

El despliegue es un proceso de múltiples pasos que involucra la configuración de varios servicios en la nube y el despliegue de un contenedor en tu propio servidor.

Consulta el archivo checklist.md para obtener una guía detallada y paso a paso sobre cómo configurar y desplegar toda la aplicación a producción.

5. Estilo de código

    Python: Usar ruff (ver pyproject.toml).

    TypeScript/JavaScript: Usar eslint y prettier.

    Mantén el estilo existente.

6. Seguridad

    Nunca incluyas secretos en el código fuente. Los secretos se gestionan de forma segura a través de los dashboards de Vercel, Cloudflare, Supabase y, para producción, en un archivo .env.prod en el servidor que aloja el gateway de WhatsApp.

7. Flujo de trabajo con Git

    Trabaja en ramas de feature (feature/nombre-descriptivo).

    Asegúrate de que las pruebas y linters pasen antes de crear un PR a main.

    El despliegue de los componentes serverless (Vercel, Cloudflare) es automático al hacer merge a main. El gateway de WhatsApp requiere un despliegue manual en el servidor.
