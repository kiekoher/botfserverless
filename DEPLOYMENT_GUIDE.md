# Guía de Despliegue a Producción de EVA

Esta guía reemplaza al `Checklist.md` original y describe el proceso de despliegue robusto y automatizado para la plataforma EVA.

## Fase 1: Configuración Inicial y Gestión de Secretos (Crítico)

Una gestión de secretos centralizada y segura es la base de un despliegue de producción. Utilizaremos [Doppler](https://doppler.com) para gestionar todas las variables de entorno y secretos de forma segura.

### 1.1. Configuración de Doppler

1.  **Crear una Cuenta:** Regístrate para obtener una cuenta gratuita en [Doppler](https://www.doppler.com/).

2.  **Crear un Proyecto:**
    *   Dentro de tu organización de Doppler, crea un nuevo proyecto llamado `eva`.
    *   Doppler creará por defecto tres entornos: `dev`, `stg`, y `prd`. Nos centraremos en `prd` para la producción.

3.  **Añadir Secretos a Doppler:**
    *   Navega al proyecto `eva` y selecciona el entorno `prd`.
    *   Añade los siguientes secretos. Los valores específicos los obtendrás de tus cuentas de Supabase, Google Cloud, Cloudflare, etc.

    ```
    # Supabase
    SUPABASE_URL
    NEXT_PUBLIC_SUPABASE_URL
    SUPABASE_ANON_KEY
    NEXT_PUBLIC_SUPABASE_ANON_KEY
    SUPABASE_SERVICE_ROLE_KEY

    # Google Cloud & AI Services
    # Nota: Para GOOGLE_APPLICATION_CREDENTIALS_JSON, copia el contenido
    # completo del archivo JSON de tu cuenta de servicio.
    GOOGLE_APPLICATION_CREDENTIALS_JSON
    OPENAI_API_KEY
    DEEPSEEK_API_KEY

    # Cloudflare R2 & Queues
    R2_BUCKET_NAME
    R2_ACCOUNT_ID
    R2_ACCESS_KEY_ID
    R2_SECRET_ACCESS_KEY
    CLOUDFLARE_QUEUE_ID

    # Vercel (URL de la API desplegada)
    # Este valor lo obtendrás después del primer despliegue en Vercel.
    # Ej: https://eva-plattform.vercel.app/api/v1
    MAIN_API_URL

    # WhatsApp Gateway
    WHATSAPP_USER_ID

    # Observability (BetterStack)
    BETTERSTACK_SOURCE_TOKEN
    BACKUP_HEARTBEAT_URL
    ```

### 1.2. Configuración de Monitores (BetterStack)

Además del logging, usaremos BetterStack para monitorizar la salud de nuestros servicios.

1.  **Monitor de Uptime (API Principal):**
    *   En el dashboard de BetterStack, ve a "Monitors" y crea uno nuevo.
    *   **Tipo:** `Website URL`.
    *   **URL:** Introduce la URL de tu aplicación en Vercel (el valor de tu secreto `MAIN_API_URL` sin la ruta `/api/v1`).
    *   **Regiones de Comprobación:** Selecciona varias regiones para evitar falsos positivos.
    *   Configura las alertas a tu gusto (email, Slack, etc.).

2.  **Monitor de Heartbeat (Backup del Gateway):**
    *   Crea otro monitor en BetterStack.
    *   **Tipo:** `Heartbeat`.
    *   **Periodo de Alerta:** Configúralo a un valor ligeramente superior a la frecuencia de tu `cron job` (ej. si el cron corre cada hora, ponlo en 1 hora y 10 minutos).
    *   BetterStack te proporcionará una URL única. **Este es el valor que debes poner en tu secreto `BACKUP_HEARTBEAT_URL` en Doppler.**
    *   El script `backup.sh` notificará a esta URL automáticamente. Si el backup falla o el cron job no se ejecuta, BetterStack te alertará.

## Fase 2: Hardening de Seguridad

Una vez configurados los servicios, es crucial asegurar los puntos de entrada y los permisos.

### 2.1. Principio de Mínimo Privilegio: Rol de IAM en Google Cloud

La cuenta de servicio de Google Cloud solo se utiliza para la API de Speech-to-Text. Asignarle el rol de "Editor" es innecesariamente permisivo. Sigue estos pasos para crear un rol personalizado con los permisos mínimos:

1.  En la consola de Google Cloud, ve a `IAM y Administración > Roles`.
2.  Haz clic en `CREAR ROL`.
3.  **Título del rol:** `Speech-to-Text API User`
4.  **ID del rol:** `speechToTextApiUser`
5.  Haz clic en `AÑADIR PERMISOS`.
6.  Filtra por `speech.recognize` y selecciona el permiso `speech.recognize`.
7.  Crea el rol.
8.  Ahora, ve a `IAM y Administración > IAM`, busca tu cuenta de servicio y asígnale este nuevo rol (`Speech-to-Text API User`) en lugar de "Editor".

### 2.2. Configuración de Firewall (ufw) en el Servidor del Gateway

El servidor Ubuntu que aloja el gateway de WhatsApp debe estar protegido por un firewall. `ufw` es una forma sencilla de lograrlo.

1.  **Conéctate a tu servidor** vía SSH.

2.  **Verifica si `ufw` está instalado** (suele venir por defecto):
    ```bash
    sudo ufw status
    ```

3.  **Añade reglas para permitir el tráfico esencial:**
    *   **SSH (para que no te quedes fuera):** `sudo ufw allow OpenSSH`
    *   **HTTP (para Traefik/Let's Encrypt si lo usas):** `sudo ufw allow http`
    *   **HTTPS (para el tráfico web normal):** `sudo ufw allow https`

4.  **Activa el firewall:**
    ```bash
    sudo ufw enable
    ```
    Confirma con `y` cuando te lo pida.

5.  **Verifica el estado final:**
    ```bash
    sudo ufw status verbose
    ```
    Deberías ver tus reglas activas. El resto del tráfico entrante será bloqueado por defecto.

## Fase 3: Automatización del Despliegue con GitHub Actions

El despliegue manual es propenso a errores. Automatizaremos el proceso usando GitHub Actions para el `whatsapp-gateway` y las migraciones de Supabase.

### 3.1. Configuración de Secretos de GitHub

Ve a la configuración de tu repositorio en GitHub > `Secrets and variables` > `Actions` y añade los siguientes secretos:

*   **`GATEWAY_SSH_HOST`**: La dirección IP o hostname de tu servidor Ubuntu.
*   **`GATEWAY_SSH_USER`**: El nombre de usuario para conectar al servidor (ej. `ubuntu`).
*   **`GATEWAY_SSH_PRIVATE_KEY`**: La clave privada SSH para acceder a tu servidor sin contraseña.
    *   **Importante:** Genera un par de claves SSH dedicado para GitHub Actions. Añade la clave pública (`.pub`) al archivo `~/.ssh/authorized_keys` de tu servidor.
*   **`DOPPLER_TOKEN_PROD`**: Un token de servicio de Doppler para el entorno de producción.
    *   En Doppler, ve a tu proyecto `eva` > `prd` > `Access` y crea un Service Token con permisos de solo lectura.
*   **`SUPABASE_ACCESS_TOKEN`**: Tu token de acceso personal de Supabase. Lo puedes generar desde `Account > Access Tokens` en tu dashboard de Supabase.
*   **`SUPABASE_PROJECT_ID`**: El ID de tu proyecto de Supabase. Lo encuentras en `Project Settings > General`.
*   **`SUPABASE_DB_PASSWORD`**: La contraseña de tu base de datos. La estableciste al crear el proyecto. Si no la recuerdas, puedes resetearla desde `Project Settings > Database`.

### 1.3. Integración con Vercel

1.  Ve al dashboard de tu proyecto en Vercel.
2.  Busca la pestaña de "Integrations" y añade la integración de Doppler.
3.  Autoriza el acceso a tu cuenta de Doppler y vincula el proyecto de Vercel con el proyecto `eva` de Doppler y el entorno `prd`.
4.  Vercel sincronizará automáticamente los secretos. Ya no es necesario añadirlos manualmente en la UI de Vercel.

### 1.3. Integración con Cloudflare

1.  Sigue la guía de Doppler para [integrar con Cloudflare Workers](https://docs.doppler.com/docs/cloudflare-workers).
2.  Esto implicará configurar el CLI de Doppler (`wrangler.toml`) para que obtenga los secretos directamente de Doppler durante el despliegue (`npx wrangler deploy`). Ya no necesitarás usar `npx wrangler secret put`.

### 1.4. Configuración del Servidor del Gateway (Ubuntu)

En lugar de usar un archivo `.env.prod`, el script de despliegue que crearemos en la Fase 3 utilizará el CLI de Doppler para inyectar los secretos directamente en el contenedor de Docker.

**Próximos pasos en el plan:** Modificar `docker-compose.prod.yml` y crear `scripts/deploy.sh` para usar `doppler run`.
