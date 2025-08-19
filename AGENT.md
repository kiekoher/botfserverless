# AGENT.md: Manifiesto del Proyecto EVA

Este documento es la fuente de verdad única y centralizada para cualquier agente de codificación de IA (como Jules o Codex) que interactúe con este repositorio. Su propósito es proporcionar todo el contexto necesario sobre la arquitectura, estructura, comandos y convenciones del proyecto.

## 1. Descripción General y Arquitectura del Proyecto

EVA es una plataforma SaaS multi-cliente para desplegar agentes de ventas de IA. El proyecto sigue una arquitectura de microservicios con un despliegue híbrido:

* **Frontend**: Una aplicación Next.js (React) desplegada en **Vercel**. Se encarga del dashboard de usuario, la gestión de agentes y la visualización de conversaciones.
* **Backend**: Un conjunto de microservicios en Python (FastAPI) y Node.js, orquestados por **Docker Compose** en un servidor dedicado.
* **API Gateway**: **Nginx** actúa como reverse proxy en el servidor, gestionando el tráfico y terminando las conexiones SSL con certificados de Let's Encrypt.
* **Comunicación Asíncrona**: **Redis Streams** se utiliza como el bus de mensajes para desacoplar los microservicios, asegurando un flujo de datos robusto y escalable.
* **Base de Datos y Autenticación**: **Supabase** (PostgreSQL con pgvector) gestiona los datos de usuarios, agentes, conversaciones y la autenticación. Se usa **Row Level Security (RLS)** en todas las tablas sensibles.
* **Almacenamiento de Archivos**: Los archivos de audio de los usuarios se almacenan en **Cloudflare R2**.

## 2. Estructura del Proyecto y Organización

La estructura del repositorio está diseñada para separar claramente las responsabilidades:

* `/frontend`: Contiene todo el código de la aplicación Next.js. El código fuente principal está en `/frontend/src`. Esta es la base de código que se despliega en Vercel.
* `/services`: Alberga todos los microservicios del backend, cada uno en su propio subdirectorio.
    * `/services/main-api`: El cerebro del sistema. Contiene el `AIRouter` que selecciona el modelo de IA adecuado para cada tarea y orquesta la lógica de negocio.
    * `/services/whatsapp-gateway`: El punto de entrada para los mensajes de los usuarios. Actúa como un puente entre la API de WhatsApp y Redis Streams.
    * `/services/transcription-worker`: Un servicio especializado que consume mensajes de audio de Redis, los transcribe usando la API de Google Speech-to-Text, y publica el texto resultante de vuelta a Redis.
* `/nginx`: Contiene la configuración de Nginx (`nginx.prod.conf`) utilizada para el reverse proxy en producción.
* `/supabase`: Almacena las migraciones de la base de datos, definiendo la estructura de tablas, políticas RLS e índices.
* `/docker-compose.prod.yml`: El archivo de orquestación para todos los servicios del backend en el entorno de producción.

## 3. Comandos de Compilación, Pruebas y Desarrollo

Para que un agente de IA pueda verificar su propio trabajo, debe usar los siguientes comandos:

#### Backend (Ejecutar en el servidor de producción)

* **Levantar todos los servicios en segundo plano:**
    ```bash
    docker-compose -f docker-compose.prod.yml up -d
    ```
* **Reconstruir y levantar los servicios (después de un cambio en el código):**
    ```bash
    docker-compose -f docker-compose.prod.yml up --build -d
    ```
* **Verificar logs de un servicio específico (ej. whatsapp-gateway):**
    ```bash
    docker-compose -f docker-compose.prod.yml logs -f whatsapp-gateway
    ```
* **Ejecutar Linter y Formateador (para `main-api`):**
    ```bash
    docker-compose -f docker-compose.prod.yml exec main-api ruff format .
    docker-compose -f docker-compose.prod.yml exec main-api ruff check . --fix
    ```
* **Ejecutar Pruebas Unitarias (para `main-api`):**
    ```bash
    docker-compose -f docker-compose.prod.yml exec main-api pytest
    ```

#### Frontend (Desplegado en Vercel)

* **Instalar dependencias:** `npm install`
* **Linting:** `npm run lint`
* **Pruebas:** `npm run test`
* **Compilación para producción (lo que hace Vercel):** `npm run build`

## 4. Estilo de Código y Convenciones

* **Python**: El código se formatea y valida con **Ruff**. Las reglas están implícitas en la configuración por defecto de la herramienta.
* **TypeScript/React**: Se utiliza **ESLint** con la configuración `next/core-web-vitals`. Usar comillas simples.
* **Git**: Los mensajes de commit deben seguir el estándar de **Conventional Commits**.

## 5. Directrices de Pruebas

* **Backend**: Las pruebas unitarias y de integración para los servicios de Python se escriben con **pytest**. Los archivos de prueba se encuentran en el directorio `tests/` de cada servicio.
* **End-to-End**: Existe un script de prueba E2E en `services/tests/end-to-end.py` que simula el flujo completo publicando un mensaje en Redis y esperando una respuesta.

## 6. Consideraciones de Seguridad

* **Secretos**: Todas las claves de API y secretos se gestionan a través del archivo `.env.prod` en el servidor y **NUNCA** deben ser comiteados al repositorio.
* **Acceso a Datos**: La base de datos en Supabase está protegida con **Row Level Security (RLS)** para asegurar que un usuario solo pueda acceder a los datos de sus propios agentes.
* **Comunicaciones**: Todo el tráfico web es forzado a **HTTPS** a través de Nginx y los certificados de Let's Encrypt.

## 7. Flujo de Trabajo con Git y Despliegue (CI/CD)

* **Frontend**: Cualquier `push` a la rama `main` dispara automáticamente un despliegue a producción en **Vercel**.
* **Backend**: El despliegue del backend es un proceso **manual** en el servidor. Después de hacer `git pull` en la rama `main`, se deben reconstruir y reiniciar los contenedores con `docker-compose -f docker-compose.prod.yml up --build -d`.
