# EVA: Plataforma Serverless de Agentes de Ventas con IA

EVA es una plataforma SaaS multi-tenant para desplegar agentes de ventas impulsados por inteligencia artificial. Este repositorio contiene la infraestructura completa de la plataforma, diseñada con una **arquitectura serverless híbrida** para máxima escalabilidad, mínimo mantenimiento y despliegue automatizado.

## Descripción General de la Arquitectura

El sistema ha sido migrado de una arquitectura monolítica de Docker a un enfoque serverless-first, combinando los mejores servicios gestionados con un único componente auto-alojado para requisitos específicos.

  - **`Frontend (Next.js)` y `API (Python/FastAPI)`:** La aplicación principal y su API de negocio se ejecutan en **Vercel**. El frontend es una aplicación Next.js, y la API se despliega como **Vercel Serverless Functions**, permitiendo un desarrollo y despliegue unificados.
  - **`Workers Asíncronos (TypeScript)`:** Los procesos de backend que requieren un procesamiento intensivo, como la transcripción de audio y la generación de embeddings, se ejecutan como **Cloudflare Workers**. Son ultrarrápidos, escalables y operan en el borde (edge) para una latencia mínima.
  - **`Gateway de WhatsApp (Node.js)`:** Es el punto de entrada para los mensajes de WhatsApp. Debido a la necesidad de mantener una sesión persistente, este es el único servicio que se ejecuta en un **contenedor Docker en un servidor propio (Ubuntu)**.
  - **`Base de Datos y Autenticación`:** Se utiliza **Supabase Cloud**, que proporciona una base de datos PostgreSQL gestionada, autenticación de usuarios y almacenamiento de objetos.
  - **`Almacenamiento de Archivos`:** **Cloudflare R2** se usa para almacenar archivos multimedia como audios y documentos, beneficiándose de costos de almacenamiento bajos y cero tarifas de egreso.
    \--   **`Cola de Mensajes`:** **Cloudflare Queues** actúa como el broker de mensajes que conecta de forma fiable la API en Vercel con los Workers en Cloudflare, garantizando una comunicación asíncrona robusta.

-----

## 🚀 Cómo Empezar

### 1\. Prerrequisitos

  - Node.js y npm/pnpm/yarn.
  - Python y pip.
  - CLI de Vercel (`npm install -g vercel`).
  - CLI de Cloudflare (`npm install -g wrangler`).
  - Una cuenta en Supabase, Cloudflare, Vercel y Google Cloud Platform.
  - Docker y Docker Compose (solo para el `whatsapp-gateway` en tu servidor).

### 2\. Variables de Entorno

El sistema se configura mediante variables de entorno gestionadas en las plataformas correspondientes (Vercel, Cloudflare). Para el desarrollo local y el despliegue del gateway, puedes usar un archivo `.env`.

Copia el archivo de ejemplo:

```bash
cp .env.prod.example .env.prod
```

Rellena los valores según las necesidades de cada servicio.

### 3\. Ejecutando el Sistema Localmente

El desarrollo local simula el entorno de producción usando las herramientas CLI de cada proveedor.

  - **Frontend y API (Vercel):**
    Desde la raíz del proyecto, inicia el entorno de desarrollo de Vercel. Esto cargará las variables de entorno locales y servirá tanto la aplicación Next.js como las funciones serverless de la API.

    ```bash
    vercel dev
    ```

  - **Workers (Cloudflare):**
    Desde el directorio `workers/`, inicia el entorno de desarrollo de Wrangler.

    ```bash
    cd workers
    wrangler dev
    ```

-----

## 🧪 Pruebas

Las pruebas son esenciales para mantener la calidad del código.

  - **Pruebas de API (Python/FastAPI):**
    Desde el directorio `api/`, ejecuta pytest.

    ```bash
    cd api
    pytest
    ```

  - **Pruebas de Frontend (Next.js):**
    Desde el directorio `frontend/`, ejecuta las pruebas de Jest/React Testing Library.

    ```bash
    cd frontend
    npm test
    ```

-----

## 🚀 Despliegue en Producción

El despliegue combina la automatización de CI/CD de las plataformas serverless con un paso manual para el componente auto-alojado.

**Para una guía completa y detallada, consulta el archivo `checklist.md`.**

### Flujo de Despliegue

1.  **Configuración de Servicios:** Sigue la Fase 1 del `checklist.md` para crear y configurar tus cuentas de Supabase, Cloudflare, Google Cloud y Vercel.
2.  **Configuración de Secretos:** Añade todas las claves de API y variables de entorno en los paneles de Vercel y Cloudflare como se indica en el `checklist.md`.
3.  **Despliegue Serverless (Automático):**
      - Conecta tu repositorio de GitHub a Vercel y Cloudflare.
      - Cada `push` a la rama `main` activará automáticamente los despliegues del frontend, la API y los workers.
4.  **Despliegue del Gateway de WhatsApp (Manual):**
      - Conéctate a tu servidor Ubuntu.
      - Ejecuta el contenedor `whatsapp-gateway` usando el `docker-compose.prod.yml` y un archivo `.env.prod` con las variables de entorno necesarias.

-----

## 💾 Backups y Recuperación

La estrategia de backups se simplifica enormemente con la arquitectura serverless.

### 1\. Base de Datos (Supabase)

Supabase gestiona los backups de forma automática en sus planes de pago.

  - **Acción Requerida:**
    1.  Asegúrate de que tu proyecto de Supabase está en un plan que incluya backups automáticos.
    2.  Familiarízate con el proceso de "Point-in-Time Recovery (PITR)" que ofrece Supabase para restauraciones.

### 2\. Datos de Sesión de WhatsApp

El único componente con estado en tu infraestructura es la sesión del `whatsapp-gateway`.

  - **Estrategia de Backup:**
    Los datos de la sesión se guardan en un volumen de Docker en tu servidor. Se recomienda implementar una rutina de backup simple (por ejemplo, un `cron job` en el host) que comprima y guarde el contenido de este volumen periódicamente en una ubicación segura.

-----

## 📄 Licencia

Este proyecto es software propietario. Todos los derechos están reservados.
