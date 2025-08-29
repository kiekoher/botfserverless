# Guía Maestra de Despliegue a Producción de EVA

**Versión:** 2.0 (Actualizada)
**Propósito:** Esta guía es la **única fuente de verdad** para la configuración, despliegue y mantenimiento de la plataforma EVA. Reemplaza a todos los documentos anteriores (`Checklist.md`, `AGENT.md` parcial).

---

## 📖 Playbook de Puesta en Producción (De Cero a Producción)

Sigue estos pasos en orden para configurar y desplegar la plataforma completa.

### **Paso 1: Configurar Cuentas de Servicios Externos**

Antes de tocar el código, necesitas cuentas en los siguientes servicios:
- [GitHub](https://github.com/) (para alojar el código y ejecutar los pipelines de CI/CD)
- [Vercel](https://vercel.com/) (para el frontend y la API)
- [Cloudflare](https://www.cloudflare.com/) (para Workers, R2 y Queues)
- [Supabase](https://supabase.com/) (para la base de datos y autenticación)
- [Doppler](https://www.doppler.com/) (para la gestión de secretos)
- [Google Cloud Platform](https://cloud.google.com/) (para la API de Speech-to-Text)
- [BetterStack](https://betterstack.com/) (para monitorización y logging)

### **Paso 2: Configurar el Servidor del Gateway**

Provisiona un servidor **Ubuntu 22.04 LTS** en tu proveedor de nube preferido (DigitalOcean, AWS, etc.). Luego, conéctate por SSH y sigue la **[Guía de Configuración del Servidor](#-guía-de-configuración-del-servidor-del-gateway)** más abajo en este documento.

### **Paso 3: Poblar el Gestor de Secretos (Doppler)**

1.  Crea un proyecto `eva` en Doppler con los entornos `dev`, `stg`, y `prd`.
2.  Navega al entorno `prd` y añade todos los secretos listados en la sección **[Lista de Secretos de Doppler](#-lista-de-secretos-de-doppler)**. Necesitarás obtener los valores de las consolas de Supabase, Cloudflare, etc.

### **Paso 4: Configurar los Secretos de GitHub Actions**

1.  En tu repositorio de GitHub, ve a `Settings > Secrets and variables > Actions`.
2.  Añade los secretos listados en la sección **[Configuración de Secretos de GitHub](#-configuración-de-secretos-de-github)**. Estos son necesarios para que el pipeline de CI/CD pueda desplegar automáticamente.

### **Paso 5: Configurar las Integraciones de Doppler**

1.  **Vercel:** En el dashboard de tu proyecto Vercel, añade la integración de Doppler y vincúlala a tu proyecto `eva` (entorno `prd`).
2.  **Cloudflare:** Sigue la guía de Doppler para [integrar con Cloudflare Workers](https://docs.doppler.com/docs/cloudflare-workers). Esto permite a `wrangler` obtener los secretos durante el despliegue.

### **Paso 6: Desplegar la Aplicación**

1.  **Despliegues Serverless (Vercel & Cloudflare):**
    *   Conecta tu repositorio de GitHub a Vercel. Vercel desplegará automáticamente el frontend (`frontend/`) y la API (`api/`) en cada push a `main`.
    *   Usa el CLI `wrangler` para desplegar los workers (`npx wrangler deploy`). La integración de Doppler se encargará de los secretos.
2.  **Despliegue del Gateway y Migraciones (Automático):**
    *   Una vez que hagas `git push` a la rama `main`, el pipeline de GitHub Actions se ejecutará automáticamente.
    *   **Verificará las pruebas** de todos los componentes.
    *   Si las pruebas pasan y hay cambios relevantes, **desplegará el gateway de WhatsApp y las migraciones de la base de datos sin intervención manual.**
    *   Puedes monitorear el progreso en la pestaña "Actions" de tu repositorio.

### **Paso 7: Configurar el Backup y la Monitorización**

1.  **Configurar Cron Job para Backups:** En el servidor del gateway, configura un cron job para ejecutar el script `scripts/backup.sh` diariamente. Esto está detallado en la **[Guía de Configuración del Servidor](#-guía-de-configuración-del-servidor-del-gateway)**.
2.  **Configurar Monitores en BetterStack:** Crea los monitores de Uptime y Heartbeat como se describe en la sección **[Monitorización con BetterStack](#-monitorización-con-betterstack)**.

---

## 🛡️ Estrategia de Backup y Recuperación de Desastres

Una estrategia de backup robusta es crítica para la continuidad del negocio. La plataforma EVA tiene dos componentes con estado que requieren backups: el **Gateway de WhatsApp** y la **Base de Datos PostgreSQL (Supabase)**.

### 1. Backup del Gateway de WhatsApp

-   **Qué se respalda:** El estado de la sesión de WhatsApp, almacenado en un volumen de Docker.
-   **Cómo funciona:** El script `scripts/backup.sh` se ejecuta diariamente a través de un cron job en el servidor del gateway. Comprime el volumen de Docker y lo sube a un bucket privado en Cloudflare R2.
-   **Monitorización:** El script notifica a un monitor de heartbeat en BetterStack. Si el backup falla, se generará una alerta.

### 2. Backup de la Base de Datos Principal (Supabase)

-   **Estrategia de Recuperación Avanzada:** Para garantizar la máxima integridad de los datos y minimizar la pérdida de información (RPO de ~2 minutos), la plataforma **requiere** el uso de la funcionalidad **Point-in-Time Recovery (PITR)** de Supabase.
-   **Justificación de Seguridad:** Los backups diarios tradicionales de Supabase presentan un objetivo de punto de recuperación (RPO) de 24 horas, lo cual es un riesgo inaceptable para una aplicación transaccional. PITR es la solución implementada para mitigar este riesgo.
-   **Requisito de Infraestructura:** La activación de PITR es un paso **obligatorio** durante la configuración y requiere una instancia de Supabase de tipo "Small" o superior. Este costo es una inversión necesaria en la seguridad de los datos.

#### **Procedimiento de Configuración y Uso de PITR**

1.  **Activación Mandatoria de PITR:**
    -   Durante la configuración inicial del proyecto en Supabase, es **obligatorio** activar el add-on de **Point-in-Time Recovery**.
    -   **Ubicación:** `Settings` > `Add-ons` en el dashboard de Supabase.
    -   **Acción:** Habilita "Point-in-Time Recovery" y configura un período de retención de **al menos 7 días**.
    -   **Nota:** Esto requiere una instancia de cómputo "Small" o superior.

2.  **Proceso de Recuperación de Datos (En caso de desastre):**
    -   La restauración se realiza desde `Database` > `Backups` > `Point in Time`.
    -   Se debe seleccionar el punto exacto en el tiempo para la restauración.
    -   **Advertencia:** La restauración es una operación destructiva que interrumpe el servicio. Procede con extrema precaución y solo después de haber leído todas las advertencias de Supabase.

**Nota Importante:** Los backups de la base de datos de Supabase **NO** incluyen los archivos almacenados en Cloudflare R2 (como los audios de los clientes). La estrategia de backup dual (script para el gateway, PITR para la BD) es esencial para una cobertura completa.

---

## ⚙️ Automatización del Despliegue (CI/CD)

El repositorio está configurado con un pipeline de GitHub Actions (`.github/workflows/deploy.yml`) que automatiza un despliegue progresivo y seguro.

- **Disparadores:** El pipeline se activa en cada `push` a la rama `main` o puede ser ejecutado manualmente.

- **Flujo del Pipeline:**
  1.  **Pruebas Unitarias:** Se ejecutan en paralelo las pruebas para la API (`test-api`), el frontend (`test-frontend`) y el gateway (`test-gateway`). Si alguna falla, el pipeline se detiene.
  2.  **Despliegue de Migraciones:** Si las pruebas de la API pasan y se detectan cambios en `supabase/migrations/`, el job `deploy-migrations` aplica los cambios al esquema de la base de datos de producción.
  3.  **Build y Push del Gateway:** En paralelo, si las pruebas del gateway pasan y hay cambios en su código, el job `build-and-push-gateway` crea una nueva imagen Docker, la etiqueta con el hash del commit y la sube al registro de contenedores de GitHub (`ghcr.io`).
  4.  **Pruebas End-to-End (E2E):** Una vez que las migraciones de la base de datos se han aplicado, el job `test-e2e` se ejecuta. Esta prueba crítica valida el flujo completo de la API (desplegada en Vercel) y su interacción con la base de datos.
  5.  **Despliegue del Gateway:** Solo si las pruebas E2E y el build del gateway han sido exitosos, el job `deploy-gateway` se conecta por SSH al servidor y ejecuta `scripts/deploy.sh`. Este script hace `docker pull` de la nueva imagen desde `ghcr.io` y reinicia el servicio.

- **Seguridad:** Un despliegue fallido en cualquier paso crítico (pruebas, build, migraciones, E2E) detendrá todo el proceso para prevenir errores en producción.

---

## 🖥️ Guía de Configuración del Servidor del Gateway

Este servidor Ubuntu auto-alojado es **únicamente** para el gateway de WhatsApp.

### 1. Hardening Inicial (Firewall)
```bash
# Permitir tráfico esencial
sudo ufw allow OpenSSH
sudo ufw allow http
sudo ufw allow https

# Activar firewall
sudo ufw enable
```

### 2. Instalación de Dependencias
```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar Docker
sudo apt install -y docker.io docker-compose

# Instalar Node.js y npm (para el script de despliegue)
sudo apt install -y nodejs npm

# Instalar AWS CLI v2 (para los backups a R2)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Instalar Doppler CLI
sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates curl gnupg
curl -sLf 'https://packages.doppler.com/public/cli/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/doppler-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/doppler-archive-keyring.gpg] https://packages.doppler.com/public/cli/deb/debian any-version main" | sudo tee /etc/apt/sources.list.d/doppler-cli.list
sudo apt-get update && sudo apt-get install doppler
```

### 3. Configuración del Repositorio
```bash
# Clonar el repositorio
git clone <URL_DE_TU_REPOSITORIO> ~/eva-platform
cd ~/eva-platform

# Crear clave SSH para GitHub Actions (si aún no lo has hecho)
ssh-keygen -t rsa -b 4096 -C "github_actions_key"
cat ~/.ssh/github_actions_key.pub >> ~/.ssh/authorized_keys
# Copia el contenido de ~/.ssh/github_actions_key para usarlo como secreto en GitHub
```

### 4. Configuración del Cron Job para Backups
1.  Abre el editor de cron del usuario **root**: `sudo crontab -e`
2.  Añade la siguiente línea para ejecutar el backup todos los días a las 3:00 AM. **Importante:** El script necesita las variables de entorno de Doppler para funcionar.
    ```crontab
    # Ejecutar el backup del gateway de WhatsApp
    0 3 * * * doppler run --project eva --config prd -- bash /home/ubuntu/eva-platform/scripts/backup.sh >> /var/log/backup.log 2>&1
    ```
    **Nota:** Se debe usar `sudo crontab -e` para que el cron job se ejecute como el usuario `root`. Esto es necesario porque el script de backup necesita permisos para leer los volúmenes de Docker (`/var/lib/docker/volumes`), que son propiedad de `root`.

---

## 🔑 Listas de Secretos y Configuraciones

### Lista de Secretos de Doppler (`prd` environment)
```
# Supabase
SUPABASE_URL
NEXT_PUBLIC_SUPABASE_URL
SUPABASE_ANON_KEY # La clave pública (anon) de Supabase. Usada por el frontend y el backend.
NEXT_PUBLIC_SUPABASE_ANON_KEY # La misma clave pública (anon) para el frontend.
SUPABASE_SERVICE_ROLE_KEY # La clave de servicio (secreta) para bypass RLS en tareas de admin.
SUPABASE_DB_PASSWORD # Contraseña de la base de datos de Postgres.
SUPABASE_JWT_SECRET # El secreto para firmar y verificar JWTs. Se encuentra en Settings > API.

# Google Cloud & AI Services
GOOGLE_APPLICATION_CREDENTIALS_JSON
OPENAI_API_KEY
DEEPSEEK_API_KEY

# Cloudflare R2, Queues & API
R2_BUCKET_NAME
R2_ACCOUNT_ID
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY
CLOUDFLARE_QUEUE_ID
CLOUDFLARE_API_TOKEN # Token de API de Cloudflare con permisos para Queues
R2_ENDPOINT_URL # Ej: https://<ACCOUNT_ID>.r2.cloudflarestorage.com

# Vercel
MAIN_API_URL
FRONTEND_URL # The public URL of the Vercel frontend. e.g. https://my-app.vercel.app

# Stripe
STRIPE_API_KEY
STRIPE_WEBHOOK_SECRET

# WhatsApp Gateway
WHATSAPP_USER_ID

# Observability (BetterStack)
BETTERSTACK_SOURCE_TOKEN # El token de tu "source" de BetterStack Logs.
BETTERSTACK_INGEST_HOST # El host de ingesta de syslog, ej: "syslog.betterstack.com". Se obtiene de la configuración de la "source".
BACKUP_HEARTBEAT_URL # La URL para el monitor de heartbeat del backup.
```

### Configuración de Secretos de GitHub
-   `GATEWAY_SSH_HOST`: IP pública del servidor del gateway.
-   `GATEWAY_SSH_USER`: `ubuntu` o el usuario que corresponda.
-   `GATEWAY_SSH_PRIVATE_KEY`: La clave SSH privada generada para Actions.
-   `DOPPLER_TOKEN_PROD`: Un token de servicio de Doppler (solo lectura).
-   `SUPABASE_ACCESS_TOKEN`: Tu token de acceso personal de Supabase.
-   `SUPABASE_PROJECT_ID`: El ID de tu proyecto de Supabase.
-   `SUPABASE_DB_PASSWORD`: La contraseña de tu base de datos de Supabase.

### Principio de Mínimo Privilegio: Rol de IAM en Google Cloud
La cuenta de servicio de Google Cloud solo necesita el permiso `speech.recognize`. Crea un rol personalizado en IAM con únicamente este permiso y asígnalo a la cuenta de servicio.

### Monitorización con BetterStack
1.  **Monitor de Uptime (API Principal):** Crea un monitor de tipo `Website URL` apuntando a la URL base de tu aplicación en Vercel.
2.  **Monitor de Heartbeat (Backup del Gateway):** Crea un monitor de tipo `Heartbeat`. BetterStack te dará una URL que debes añadir al secreto `BACKUP_HEARTBEAT_URL` en Doppler. El script de backup notificará a esta URL. Si no lo hace, recibirás una alerta.
