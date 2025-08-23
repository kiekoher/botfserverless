# EVA: Plataforma de Agentes de Ventas con IA

EVA es una plataforma SaaS multi-tenant para desplegar agentes de ventas impulsados por inteligencia artificial. Este repositorio contiene la infraestructura completa y contenerizada de la plataforma, diseñada para un despliegue automatizado y escalable.

El sistema sigue una arquitectura de microservicios y está completamente orquestado por Docker Compose. Todos los servicios, incluido el frontend, están diseñados para ejecutarse en un único servidor de producción.

## Descripción General de la Arquitectura

-   **`frontend` (Next.js):** El panel de control orientado al usuario para gestionar agentes, ver conversaciones y configurar cuentas. Se sirve como un contenedor Docker.
-   **`main-api` (Python/FastAPI):** El núcleo de la aplicación. Maneja toda la lógica de negocio, gestiona el enrutamiento de modelos de IA y sirve la API REST principal. Se comunica con otros servicios de forma asíncrona.
-   **`whatsapp-gateway` (Node.js):** El punto de entrada para todos los mensajes de usuario desde WhatsApp. Actúa como un puente, recibiendo mensajes, subiendo archivos multimedia y publicando eventos en un stream de Redis.
-   **`transcription-worker` (Python):** Un trabajador dedicado que escucha los mensajes de audio en el stream de Redis, los transcribe usando un modelo local `faster-whisper` para garantizar la privacidad y un costo fijo, y publica el texto de vuelta para que `main-api` lo procese.
-   **`traefik` (Traefik):** Un proxy inverso que enruta el tráfico entrante al servicio apropiado (`frontend` o `main-api`) y maneja la terminación SSL con certificados auto-renovables de Let's Encrypt.
-   **`redis` (Redis):** Utilizado como un message broker de alto rendimiento (a través de Redis Streams) para facilitar la comunicación asíncrona entre los microservicios.
-   **`loki` & `promtail`:** Una pila de logging completa para agregar y ver los logs de todos los contenedores en ejecución.

---

## 🚀 Cómo Empezar

### 1. Prerrequisitos

-   Docker & Docker Compose
-   Un nombre de dominio registrado que apunte a la dirección IP de su servidor.
-   Una cuenta de Docker Hub para el almacenamiento de imágenes.

### 2. Variables de Entorno

Todo el sistema se configura mediante variables de entorno. Para desarrollo local o producción, copie el archivo de ejemplo:

```bash
cp .env.example .env.prod
```

Luego, complete los valores en `.env.prod`. Consulte los comentarios en el archivo como guía para cada variable. Para cambiar los modelos usados por Gemini, establezca `GEMINI_EMBED_MODEL` y `GEMINI_CHAT_MODEL`.

Estas variables controlan:

- `GEMINI_EMBED_MODEL`: modelo utilizado para generar embeddings.
- `GEMINI_CHAT_MODEL`: modelo utilizado para respuestas conversacionales.
- `NEXT_PUBLIC_API_URL`: URL base de la API que el frontend usará para sus solicitudes.

### 3. Ejecutando el Sistema Localmente

Para construir y ejecutar todos los servicios en modo detached, use el archivo docker-compose de producción, que es la única fuente de verdad para la arquitectura del proyecto:

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

Para ver los logs de un servicio específico (por ejemplo, `whatsapp-gateway` para escanear el código QR):

```bash
docker-compose -f docker-compose.prod.yml logs -f whatsapp-gateway
```

---

## 🧪 Pruebas

El proyecto incluye una suite de pruebas automatizadas tanto para el backend como para el frontend, que se ejecuta automáticamente en el pipeline de CI/CD.

Para correr las pruebas de backend fuera de contenedores, instale las dependencias necesarias y ejecute `pytest`:

```bash
pip install -r requirements.txt
pytest
```

Para ejecutar las pruebas manualmente dentro de los contenedores, primero asegúrese de que los servicios estén en funcionamiento:

```bash
# Iniciar todos los servicios
docker-compose -f docker-compose.prod.yml up -d

# Esperar unos segundos para que los servicios se inicien, luego ejecutar las pruebas
```

-   **Pruebas de Backend (`main-api`):**
    ```bash
    docker-compose -f docker-compose.prod.yml exec main-api pytest
    ```

-   **Pruebas de Frontend:**
    ```bash
    docker-compose -f docker-compose.prod.yml exec frontend npm test
    ```

---

## 🚀 Despliegue en Producción (CI/CD)

Este proyecto está configurado para **despliegues totalmente automatizados** a un entorno de producción usando GitHub Actions.

### Cómo Funciona

El pipeline de despliegue está definido en `.github/workflows/deploy.yml` y se activa en cada push a la rama `main`. Consta de tres etapas:

1.  **Test y Lint:** Ejecuta automáticamente todas las pruebas y verificaciones de calidad de código para todos los servicios. Este trabajo debe pasar antes de que el despliegue pueda continuar.
2.  **Build y Push:** Construye nuevas imágenes de Docker para todos los servicios, las etiqueta con `latest` y las sube a su registro de Docker Hub.
3.  **Deploy:** Se conecta al servidor de producción a través de SSH, crea el archivo `.env.prod` a partir de los GitHub Secrets, descarga las últimas imágenes de Docker desde Docker Hub y reinicia los servicios usando `docker-compose.prod.yml`.

### Configuración de GitHub Secrets

Para que la automatización funcione, debe configurar los siguientes secrets en la configuración de su repositorio de GitHub en **Settings > Secrets and variables > Actions**:

-   `DOCKERHUB_USERNAME`: Su nombre de usuario de Docker Hub.
-   `DOCKERHUB_TOKEN`: Un token de acceso de Docker Hub con permisos de lectura/escritura.
-   `SSH_HOST`: La dirección IP o el dominio de su servidor de producción.
-   `SSH_USERNAME`: El nombre de usuario para el acceso SSH.
-   `SSH_PRIVATE_KEY`: La clave SSH privada para acceder al servidor.
-   `DOMAIN_NAME`: El nombre de dominio para su servicio (por ejemplo, `eva.yourcompany.com`).
-   `CERTBOT_EMAIL`: La dirección de correo electrónico para las notificaciones de Let's Encrypt.
-   Todos los demás secrets requeridos por la aplicación (por ejemplo, `SUPABASE_URL`, `GOOGLE_API_KEY`, etc.).

Con esta configuración, su infraestructura está totalmente automatizada. Simplemente haga push a `main`, y sus cambios serán probados y desplegados.
