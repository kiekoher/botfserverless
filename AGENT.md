# AGENT.md: Manifiesto del Proyecto EVA

Este documento es la fuente de verdad única y centralizada para cualquier agente de codificación de IA (como Jules o Codex) que interactúe con este repositorio. Su propósito es proporcionar todo el contexto necesario sobre la arquitectura, estructura, comandos y convenciones del proyecto.

## 1. Descripción General y Arquitectura

EVA es una plataforma SaaS multi-cliente para desplegar agentes de ventas de IA. El proyecto sigue una arquitectura de microservicios, completamente orquestada por Docker Compose para un despliegue unificado en un único servidor.

*   **Arquitectura Unificada:** Todos los servicios, **incluido el frontend**, se ejecutan como contenedores Docker en el mismo entorno, gestionados por `docker-compose.prod.yml`.
*   **`traefik`:** Actúa como el reverse proxy. Enruta el tráfico entrante a los servicios correspondientes (`frontend`, `main-api`) basándose en reglas definidas en etiquetas de Docker. Gestiona automáticamente la obtención y renovación de certificados SSL/TLS de Let's Encrypt.
*   **`frontend` (Next.js):** El dashboard de usuario para gestionar agentes y visualizar conversaciones. Se sirve a través del reverse proxy Traefik.
*   **`main-api` (Python/FastAPI):** El cerebro del sistema. Gestiona la lógica de negocio, el enrutamiento de modelos de IA y la API REST principal. Utiliza un cliente Redis asíncrono para no bloquear el event loop.
*   **`whatsapp-gateway` (Node.js):** El punto de entrada para los mensajes de WhatsApp. Publica eventos en un stream de Redis.
*   **`transcription-worker` (Python):** Un servicio que consume eventos de audio de Redis, los transcribe y publica el texto resultante en otro stream. También es completamente asíncrono.
*   **`redis`:** Actúa como un message broker de alto rendimiento utilizando Redis Streams.

## 2. Estructura del Proyecto

*   `/frontend`: Contiene la aplicación Next.js.
*   `/services`: Contiene todos los microservicios del backend (`main-api`, `whatsapp-gateway`, `transcription-worker`).
*   `/supabase`: Almacena las migraciones de la base de datos.
*   `/docker-compose.prod.yml`: **El único archivo de orquestación.** Define todos los servicios y sus interacciones, incluyendo la configuración de enrutamiento de Traefik a través de etiquetas.
*   `/.github/workflows/deploy.yml`: Define el pipeline de CI/CD completamente automatizado.

## 3. Comandos de Compilación y Pruebas

Para que un agente de IA pueda verificar su propio trabajo, debe usar los siguientes comandos desde la raíz del repositorio. **Siempre se debe usar el archivo `docker-compose.prod.yml`.**

*   **Levantar todos los servicios en segundo plano:**
    ```bash
    docker-compose -f docker-compose.prod.yml up --build -d
    ```
*   **Verificar logs de un servicio:**
    ```bash
    docker-compose -f docker-compose.prod.yml logs -f <nombre-del-servicio>
    ```
*   **Ejecutar Linters y Pruebas (como en el CI):**
    ```bash
    # Backend Linter y Pruebas
    docker-compose -f docker-compose.prod.yml exec main-api pytest
    docker-compose -f docker-compose.prod.yml exec main-api ruff check . --fix

    # Frontend Linter y Pruebas
    docker-compose -f docker-compose.prod.yml exec frontend npm run lint
    docker-compose -f docker-compose.prod.yml exec frontend npm test
    ```

## 4. Estilo de Código y Convenciones

*   **Python**: Formateado con **Ruff**. Usar `ruff format .` y `ruff check . --fix`.
*   **TypeScript/React**: Formateado con **ESLint** (`npm run lint`).
*   **Git**: Los mensajes de commit deben seguir el estándar de **Conventional Commits**.

## 5. Flujo de Trabajo y Despliegue (CI/CD)

*   **El despliegue es 100% automatizado.**
*   Cualquier `push` a la rama `main` dispara el pipeline de GitHub Actions definido en `.github/workflows/deploy.yml`.
*   El pipeline realiza las siguientes acciones:
    1.  **Ejecuta todas las pruebas y linters.**
    2.  **Construye y publica** nuevas imágenes de Docker para cada servicio en Docker Hub.
    3.  **Se conecta por SSH** al servidor de producción, crea el archivo `.env.prod` a partir de los GitHub Secrets, descarga las nuevas imágenes y reinicia los servicios.
*   **No existe un proceso de despliegue manual.** La única fuente de verdad para el despliegue es el workflow de GitHub Actions.
