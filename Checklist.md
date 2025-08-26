Checklist de Despliegue a Producción (Serverless Híbrido)

Sigue esta guía paso a paso para configurar y desplegar todos los servicios de la plataforma EVA. Marca cada tarea a medida que la completes.

Fase 1: Configuración de Servicios Cloud y Cuentas

    [ ] Cuenta de Supabase:

        [ ] Crear un nuevo proyecto en supabase.com.

        [ ] Guardar de forma segura la URL del proyecto, la clave anon y la clave service_role.

        [ ] Ir al editor de SQL y ejecutar el contenido de todos los archivos del directorio /supabase/migrations para configurar la base de datos.

    [ ] Cuenta de Google Cloud Platform:

        [ ] Crear un nuevo proyecto en la consola de Google Cloud.

        [ ] Buscar y activar la API de Speech-to-Text.

        [ ] Crear una "Cuenta de Servicio" (Service Account).

        [ ] Asignarle el rol "Editor" (o uno más restrictivo que permita el uso de la API Speech-to-Text).

        [ ] Crear una clave para esta cuenta de servicio y descargar el archivo de credenciales JSON.

    [ ] Cuenta de Cloudflare:

        [ ] R2 Storage:

            [ ] Crear un nuevo "bucket" en Cloudflare R2.

            [ ] Guardar el nombre del bucket.

            [ ] Crear un token de API para R2 con permisos de Lectura y Escritura.

            [ ] Guardar el Account ID, Access Key ID y Secret Access Key.

        [ ] Queues:

            [ ] Crear una nueva "cola" en Cloudflare Queues.

            [ ] Guardar el ID de la cola.

        [ ] Workers:

            [ ] Instalar el CLI de Cloudflare (wrangler) en tu máquina de desarrollo (npm install -g wrangler).

            [ ] Configurar las credenciales de tu cuenta con wrangler login.

    [ ] Cuenta de Vercel:

        [ ] Crear una cuenta en vercel.com e importar tu repositorio de GitHub.

        [ ] En la configuración del proyecto, establecer el "Root Directory" a frontend.

Fase 2: Configuración de Variables de Entorno (Secretos)

    [ ] Cloudflare Workers:

        [ ] Navegar al directorio /workers en tu terminal.

        [ ] Añadir los secretos necesarios usando los siguientes comandos (reemplaza los valores):
        Bash

        npx wrangler secret put SUPABASE_URL
        npx wrangler secret put SUPABASE_SERVICE_ROLE_KEY
        npx wrangler secret put R2_BUCKET_NAME
        npx wrangler secret put R2_ACCOUNT_ID
        npx wrangler secret put R2_ACCESS_KEY_ID
        npx wrangler secret put R2_SECRET_ACCESS_KEY
        npx wrangler secret put GOOGLE_APPLICATION_CREDENTIALS_JSON

        Nota: Para el secreto de Google, copia y pega el contenido completo del archivo JSON cuando se te solicite en la terminal.

    [ ] Vercel:

        [ ] Ir al panel de configuración de tu proyecto en Vercel -> "Environment Variables".

        [ ] Añadir las siguientes variables con los secretos que guardaste:

            NEXT_PUBLIC_SUPABASE_URL

            NEXT_PUBLIC_SUPABASE_ANON_KEY

            SUPABASE_SERVICE_ROLE_KEY

            R2_BUCKET_NAME

            R2_ACCOUNT_ID

            R2_ACCESS_KEY_ID

            R2_SECRET_ACCESS_KEY

            CLOUDFLARE_QUEUE_ID

            GOOGLE_APPLICATION_CREDENTIALS_JSON (pega aquí el contenido completo del archivo JSON).

Fase 3: Despliegue de Servicios

    [ ] Cloudflare Workers:

        [ ] Desde el directorio /workers, ejecuta el comando para desplegar:
        Bash

    npx wrangler deploy

[ ] Vercel Frontend & API:

    [ ] Vercel desplegará automáticamente la última versión de tu rama main. Para forzar un nuevo despliegue, puedes hacerlo desde el dashboard de Vercel.

    [ ] Una vez desplegado, guarda la URL de producción (ej: https://mi-proyecto.vercel.app).

[ ] Gateway de WhatsApp (Tu Servidor Ubuntu):

    [ ] Conectarse a tu servidor Ubuntu.

    [ ] Asegurarse de que Docker y Docker Compose están instalados.

    [ ] Clonar el repositorio del proyecto.

    [ ] Navegar a la raíz del proyecto y crear un archivo .env.prod.

    [ ] Editar .env.prod y añadir la siguiente variable con la URL de Vercel:

    MAIN_API_URL=https://<tu-url-de-vercel>.app/api/v1

    [ ] Levantar el contenedor del gateway en modo detached (background):
    Bash

docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d whatsapp-gateway

[ ] Monitorizar los logs para escanear el código QR e iniciar sesión:
Bash

        docker logs -f <nombre_del_contenedor_de_whatsapp>

        El nombre del contenedor lo puedes obtener con docker ps.

Fase 4: Verificación Final del Sistema

    [ ] Acceder a tu URL de Vercel y verificar que el dashboard carga y puedes iniciar sesión.

    [ ] Enviar un mensaje de audio por WhatsApp al número configurado.

    [ ] Verificar en Supabase: La conversación y el mensaje deben aparecer en las tablas correspondientes.

    [ ] Verificar en Cloudflare R2: El archivo de audio .ogg debe existir en el bucket.

    [ ] Verificar en Cloudflare Workers: Los logs del transcription-worker deben mostrar una ejecución exitosa.

    [ ] Verificar en Supabase (de nuevo): El campo transcription del mensaje debe contener ahora el texto del audio.

    [ ] Verificar Respuesta: El agente de IA debe procesar el texto y enviar una respuesta a través de WhatsApp.
