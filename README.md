# EVA: Plataforma de Agentes de Ventas con IA

EVA es una plataforma SaaS multi-tenant para desplegar agentes de ventas impulsados por inteligencia artificial. Este repositorio contiene la infraestructura completa y contenerizada de la plataforma, diseñada para un despliegue automatizado y escalable.

El sistema sigue una arquitectura de microservicios y está completamente orquestado por Docker Compose. Todos los servicios, incluido el frontend, están diseñados para ejecutarse en un único servidor de producción.

## Descripción General de la Arquitectura

-   **`frontend` (Next.js):** El panel de control orientado al usuario para gestionar agentes, ver conversaciones y configurar cuentas. Se sirve como un contenedor Docker.
-   **`main-api` (Python/FastAPI):** El núcleo de la aplicación. Maneja toda la lógica de negocio, gestiona el enrutamiento de modelos de IA y sirve la API REST principal. Se comunica con otros servicios de forma asíncrona.
-   **`whatsapp-gateway` (Node.js):** El punto de entrada para todos los mensajes de usuario desde WhatsApp. Actúa como un puente, recibiendo mensajes, subiendo archivos multimedia y publicando eventos en un stream de Redis. **Nota:** Este servicio utiliza la librería `whatsapp-web.js`, que no es una API oficial de WhatsApp. Su uso ha sido evaluado y aceptado como un riesgo de negocio para la fase actual del proyecto.
-   **`transcription-worker` (Python):** Un trabajador dedicado que escucha los mensajes de audio en el stream de Redis, los transcribe usando un modelo local `faster-whisper` para garantizar la privacidad y un costo fijo, y publica el texto de vuelta para que `main-api` lo procese.
-   **`embedding-worker` (Python):** Procesa documentos entrantes, genera embeddings y actualiza el estado de los archivos en Supabase.
-   **`dlq-monitor` (Python):** Supervisa la Dead Letter Queue en Redis y registra los mensajes fallidos para su posterior análisis.
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
- `NEXT_PUBLIC_API_URL`: URL base de la API (por ejemplo `http://main-api:8000/api/v1`).
- `OPENAI_EMBED_MODEL`: modelo de embeddings usado por los servicios que consumen OpenAI (por defecto `text-embedding-3-large`).

### 3. Ejecutando el Sistema Localmente

Para construir y ejecutar todos los servicios en modo detached, use el archivo docker-compose de producción, que es la única fuente de verdad para la arquitectura del proyecto:

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

Para ver los logs de un servicio específico (por ejemplo, `whatsapp-gateway` para escanear el código QR):

```bash
docker-compose -f docker-compose.prod.yml logs -f whatsapp-gateway
```

## 📚 Documentación de la API

El servicio `main-api` expone documentación interactiva generada automáticamente por FastAPI en la ruta `/docs`.
Una vez que los contenedores estén en ejecución, puede accederse a través de:

```
http://<host>:8000/docs
```

Esta interfaz permite explorar los endpoints disponibles y probarlos directamente desde el navegador.

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
-   `GRAFANA_BASIC_AUTH_USER`: Credenciales para la autenticación básica de Grafana (formato `user:hashed_password`).
-   Todos los demás secrets requeridos por la aplicación (por ejemplo, `SUPABASE_URL`, `GOOGLE_API_KEY`, etc.).

Con esta configuración, su infraestructura está totalmente automatizada. Simplemente haga push a `main`, y sus cambios serán probados y desplegados.

---

## 💾 Backups y Recuperación

Una estrategia de backups robusta es crítica para la resiliencia de la plataforma. A continuación se describe el plan de backups para los dos componentes con estado del sistema: la base de datos de Supabase y los volúmenes de Docker.

### 1. Base de Datos (Supabase)

Supabase proporciona backups automáticos diarios en sus planes de pago.

-   **Acción Requerida:**
    1.  Asegúrese de que su proyecto de Supabase está en un plan que incluya backups automáticos.
    2.  Vaya al **Dashboard de su proyecto > Database > Backups**.
    3.  Verifique que los backups diarios están activados.
    4.  Familiarícese con el proceso de "Point-in-Time Recovery (PITR)" que ofrece Supabase para restaurar la base de datos a un punto específico en el tiempo.

### 2. Volúmenes de Docker (Redis y Sesión de WhatsApp)

Los datos de la sesión de WhatsApp y los datos de Redis (si la persistencia está habilitada) se guardan en volúmenes de Docker en el servidor host.

-   **Estrategia de Backup Automatizada:**
    El sistema incluye un servicio de backup (`backup`) totalmente automatizado y contenerizado que se ejecuta diariamente a las 3:00 AM UTC. Este servicio se encarga de:
    1.  Detener de forma segura los servicios con estado (`redis`, `whatsapp-gateway`, etc.).
    2.  Crear un archivo `.tar.gz` comprimido con los datos de los volúmenes de Docker.
    3.  Reiniciar los servicios detenidos inmediatamente después de la copia.
    4.  (Opcional) Subir el backup a un almacenamiento externo compatible con S3 (como Cloudflare R2) usando `rclone`.
    5.  Rotar y eliminar los backups locales antiguos para evitar que el disco se llene.

-   **Acción Requerida:**
    1.  **No se requiere configuración manual de `cron` en el host.** El proceso está 100% gestionado dentro del entorno de Docker.
    2.  Para activar los backups externos, configure las variables de entorno `R2_BUCKET_PATH`, `R2_REMOTE_NAME` y las credenciales de `rclone` correspondientes en su archivo `.env.prod`.

---

## 📄 Licencia

Este proyecto se distribuye bajo la licencia [MIT](LICENSE).
