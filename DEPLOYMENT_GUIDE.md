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

## ⚙️ Automatización del Despliegue (CI/CD)

El repositorio está configurado con un pipeline de GitHub Actions (`.github/workflows/deploy.yml`) que automatiza las tareas de prueba y despliegue.

- **Disparadores:** El pipeline se activa en cada `push` a la rama `main` o puede ser ejecutado manualmente.
- **Jobs de Prueba:**
  1.  `test-api`: Ejecuta `pytest` para la API de Python.
  2.  `test-frontend`: Ejecuta `npm test` para la aplicación Next.js.
  3.  `test-gateway`: Ejecuta `npm test` para el servicio de gateway de Node.js.
- **Jobs de Despliegue (Condicionales):**
  1.  `deploy-gateway`: Si las pruebas del gateway pasan y hay cambios en sus archivos, se conecta por SSH al servidor y ejecuta `scripts/deploy.sh`.
  2.  `deploy-migrations`: Si las pruebas de la API pasan y hay nuevas migraciones, aplica las migraciones a la base de datos de Supabase.

**Un despliegue fallido en cualquier paso detendrá todo el proceso para prevenir errores en producción.**

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
1.  Abre el editor de cron: `crontab -e`
2.  Añade la siguiente línea para ejecutar el backup todos los días a las 3:00 AM. **Importante:** El script necesita las variables de entorno de Doppler para funcionar.
    ```crontab
    # Ejecutar el backup del gateway de WhatsApp
    0 3 * * * doppler run --project eva --config prd -- bash /home/ubuntu/eva-platform/scripts/backup.sh >> /var/log/backup.log 2>&1
    ```

---

## 🔑 Listas de Secretos y Configuraciones

### Lista de Secretos de Doppler (`prd` environment)
```
# Supabase
SUPABASE_URL
NEXT_PUBLIC_SUPABASE_URL
SUPABASE_ANON_KEY
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
SUPABASE_DB_PASSWORD # Mover la contraseña de la DB aquí también

# Google Cloud & AI Services
GOOGLE_APPLICATION_CREDENTIALS_JSON
OPENAI_API_KEY
DEEPSEEK_API_KEY

# Cloudflare R2 & Queues
R2_BUCKET_NAME
R2_ACCOUNT_ID
R2_ACCESS_KEY_ID
R2_SECRET_ACCESS_KEY
CLOUDFLARE_QUEUE_ID
R2_ENDPOINT_URL # Ej: https://<ACCOUNT_ID>.r2.cloudflarestorage.com

# Vercel
MAIN_API_URL

# WhatsApp Gateway
WHATSAPP_USER_ID

# Observability (BetterStack)
BETTERSTACK_SOURCE_TOKEN
BACKUP_HEARTBEAT_URL
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
