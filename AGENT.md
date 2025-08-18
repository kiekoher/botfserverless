# AGENT.MD: Constitución del Proyecto y Directiva de Refactorización Autónoma (Revisión Post-Refactorización)

Hola Jules.

Este documento es tu directiva principal. Ha sido actualizado para reflejar la arquitectura final del proyecto tras la refactorización. El objetivo es mantener la base de código alineada con los principios y la estructura aquí definidos.

## 1. Arquitectura de Destino: El Manifiesto

La arquitectura del sistema se basa en un patrón de microservicios con una clara separación de responsabilidades.

*   **`backend` (Python/FastAPI) - El Núcleo Limpio:**
    *   **Ubicación:** `/backend`
    *   **Principio No Negociable:** Arquitectura Limpia (Hexagonal).
        *   `backend/app/core`: Contiene la lógica de negocio pura (casos de uso, entidades). No depende de ningún framework.
        *   `backend/app/api`: Endpoints de FastAPI que actúan como adaptadores de entrada. Reciben peticiones HTTP, las validan y orquestan los casos de uso.
        *   `backend/app/infrastructure`: Adaptadores de salida que gestionan la comunicación con servicios externos (Supabase, Google Gemini API).

*   **`whatsapp` (Node.js/whatsapp-web.js) - El Adaptador de Comunicación:**
    *   **Ubicación:** `/whatsapp`
    *   **Principio No Negociable:** Este servicio es un "adaptador de entrada" delgado. Su única responsabilidad es conectar con WhatsApp, recibir mensajes, llamar al `backend` vía API REST para procesar la lógica, y devolver la respuesta al usuario.
    *   **Cero lógica de negocio:** Toda la lógica de negocio reside en el servicio `backend`.
    *   **Tácticas Anti-Detección:** Implementa configuraciones de Puppeteer y retrasos de comportamiento para simular una interacción humana y mejorar la estabilidad de la sesión.

*   **`nginx` (Nginx) - El Enrutador:**
    *   **Ubicación:** `/nginx`
    *   **Responsabilidad:** Actúa como un reverse proxy. Enruta todo el tráfico dirigido a `/api/` hacia el servicio `backend`.

## 2. Estructura de Directorios de Destino

La estructura de archivos del proyecto es la siguiente:

```
/
├── .env.example
├── AGENT.md            # Este archivo.
├── docker-compose.yml
├── README.md
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── infrastructure/
│   │   ├── models/
│   │   └── main.py
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
│
├── whatsapp/
│   ├── bot.js
│   ├── Dockerfile
│   └── package.json
│
└── nginx/
    ├── nginx.conf
    └── Dockerfile
```

## 3. Comandos de Verificación y Validación

Estos son los comandos que DEBES ejecutar para validar la integridad del sistema.

*   **Entorno Global (Docker):**
    *   Levantar el sistema: `docker-compose up --build -d`
    *   Acceder a un servicio: `docker-compose exec <backend|whatsapp> bash`

*   **Backend (Python):**
    *   Verificación de Calidad de Código: `docker-compose exec backend ruff format . && docker-compose exec backend ruff check . --fix`
    *   Ejecución de Pruebas: `docker-compose exec backend pytest`

*   **WhatsApp (Node.js):**
    *   Instalar dependencias (si se modifica `package.json`): `docker-compose exec whatsapp npm install`

## 4. Estilo de Código y Convenciones

*   **Backend (Python/FastAPI):**
    *   Type Hinting Estricto.
    *   Inyección de Dependencias con `Depends` de FastAPI.
    *   Uso de importaciones absolutas (`app.core...`) dentro del código de la aplicación.

*   **WhatsApp (Node.js):**
    *   Uso de `async/await` para todo el flujo asíncrono.
    *   Las variables de entorno deben cargarse usando `dotenv`.

## 5. Directrices de Pruebas

*   **Pruebas Unitarias/Integración (Backend):** Todas las funcionalidades del núcleo (`core`) y de la capa de API (`api`) deben tener pruebas. Los adaptadores de infraestructura (`infrastructure`) deben ser mockeados en las pruebas de los casos de uso.
*   **Pruebas E2E:** El flujo de conversación completo se debe probar manualmente enviando un mensaje al número de WhatsApp conectado y verificando que se reciba una respuesta coherente del backend.

## 6. Seguridad

*   **Secretos:** Todas las claves de API y credenciales deben cargarse desde variables de entorno (`.env`) y nunca estar hardcodeadas.
*   **Consultas a la DB:** Las interacciones con la base de datos deben estar parametrizadas para evitar inyecciones SQL.
