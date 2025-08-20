Claro, he añadido una sección detallada sobre el flujo de onboarding al `AGENT.md` de Jules. Este flujo está diseñado para ser una guía paso a paso que asegura que un nuevo usuario pueda configurar y lanzar su agente de manera eficiente y completa.

Aquí está el documento actualizado:

---

### **`AGENT.md`**

# **Agent Persona: Jules**

Este documento define la misión, la hoja de ruta de implementación y los principios técnicos del agente "Jules". Jules es un ecosistema de IA conversacional diseñado para la excelencia en ventas, construido sobre una base tecnológica robusta y escalable.

## **Misión Principal**

La misión de Jules es convertirse en la plataforma definitiva para desplegar agentes de ventas de IA de élite. Esto se logrará a través de un **núcleo de IA multi-modelo** de rendimiento óptimo y un **dashboard de gestión intuitivo y profesional** que abstraiga toda la complejidad técnica para el usuario final.

## **Plan de Evolución Tecnológica**

Para alcanzar esta misión, se ejecutará un plan de dos fases centrado en la consolidación del backend de IA y la profesionalización del frontend.

### **1. Evolución del Frontend (Dashboard)**

Se potenciará el dashboard existente para convertirlo en un centro de control de calidad de producción.

* **Estado Actual:**
    * El frontend está construido con **Next.js**, **TypeScript** y **Tailwind CSS**.
    * Utiliza el App Router de Next.js para el enrutamiento basado en directorios.
    * La autenticación de usuarios se gestiona a través de un middleware y el cliente de **Supabase**.

* **Próximos Pasos y Decisiones de Implementación:**

    1.  **Adoptar TanStack React Query para la Gestión del Estado del Servidor:**
        * **Decisión:** Se integrará `@tanstack/react-query` como la solución estándar para manejar el fetching, cacheo y sincronización de datos con la API. Esto eliminará la gestión manual de estados de carga/error y proporcionará una experiencia de usuario más fluida y optimista.

    2.  **Expandir la Estructura de Páginas del Dashboard:**
        * **Decisión:** Se crearán las siguientes páginas y sus componentes asociados dentro del directorio `/dashboard`, siguiendo la estructura del App Router:
            * `/knowledge`: Para la gestión de la base de conocimiento del agente (subida y listado de documentos).
            * `/config`: Para la configuración detallada del comportamiento del agente.
            * `/quality`: Para la auditoría y análisis de calidad de las conversaciones.
            * `/billing`: Para la gestión de la facturación y suscripción del cliente.
            * `/onboarding`: Una guía paso a paso para nuevos clientes.
            * `/reports/opportunity-briefs`: Página para visualizar resúmenes de oportunidades de venta.
            * `/reports/performance-log`: Un registro detallado del rendimiento del agente.
            * `/reports/executive-summaries`: Informes ejecutivos consolidados.

    3.  **Centralizar la Lógica de Acceso a la API:**
        * **Decisión:** Se creará un directorio `src/services` o `src/lib/api` para centralizar todas las funciones que interactúan con la API del backend. Cada función utilizará el token de sesión de Supabase para realizar llamadas autenticadas, similar al enfoque del frontend de EVA.

    4.  **Implementar un Diseño Profesional y Coherente:**
        * **Decisión:** La UI/UX se refinará aplicando principios de diseño profesional. Se establecerá un sistema de diseño basado en una **retícula consistente, jerarquía tipográfica clara y espaciado predecible**, inspirándose en los conceptos del libro "Thinking with Type" para garantizar una interfaz de alta calidad.

### **2. Consolidación del Núcleo de IA ("Santo Grial")**

Se optimizará el motor de IA para maximizar el rendimiento y minimizar los costos, utilizando el mejor modelo para cada tarea específica.

* **Estado Actual:**
    * El backend ya cuenta con un `ai_router.py` en la `main-api`.
    * El router tiene la capacidad de interactuar con múltiples proveedores de IA, incluyendo **Gemini, DeepSeek y OpenAI** a través de sus respectivos adaptadores.

* **Próximos Pasos y Decisiones de Implementación:**

    1.  **Especialización de Modelos por Tarea:**
        * **Decisión:** Se refinará la lógica del `ai_router.py` para asignar modelos específicos a tareas concretas, materializando la arquitectura "Santo Grial":
            * **Comunicación con el Cliente:** Se utilizará **Gemini 1.5 Flash** por su bajo costo y alta velocidad, ideal para interacciones en tiempo real.
            * **Extracción de Datos (JSON):** Se usará **DeepSeek-Chat** por su excelente rendimiento en seguimiento de instrucciones y generación de formatos estructurados a un costo mínimo.
            * **Análisis y Auditoría (Backend):** Se empleará **DeepSeek-V2** en los workers de análisis por su gran capacidad analítica y bajo costo para tareas asíncronas que no impactan la latencia del usuario.

    2.  **Estandarización del Motor de Embeddings para RAG:**
        * **Decisión:** Para garantizar la máxima calidad en el sistema de Retrieval-Augmented Generation (RAG), se utilizará **`text-embedding-3-large` de OpenAI** como el motor de embeddings estándar. Se implementará la lógica necesaria para que el worker de embeddings utilice este modelo para procesar todos los documentos de la base de conocimiento.

    3.  **Implementación de Transcripción de Audio Local:**
        * **Decisión:** Para asegurar la privacidad y un costo fijo, se utilizará un modelo local **`faster-whisper`** en el worker de transcripción para procesar los mensajes de audio.

### **3. Flujo de Onboarding del Cliente**

Para garantizar una experiencia de usuario fluida y una correcta configuración inicial, se implementará un flujo de onboarding guiado en el dashboard. Este proceso se presentará a los nuevos usuarios la primera vez que inicien sesión y estará siempre accesible desde la página `/onboarding`.

**Objetivo:** Guiar al usuario a través de los 4 pasos esenciales para que su agente sea completamente funcional.

* **Paso 1: ¡Bienvenido a Bordo! - Conecta tu Canal**
    * **Acción del Usuario:** El usuario deberá conectar su cuenta de WhatsApp. La interfaz mostrará un código QR generado por el `whatsapp-gateway` para que lo escanee con su teléfono.
    * **Verificación:** El sistema confirmará en tiempo real cuando la conexión se haya establecido correctamente.
    * **Estado:** Es el paso más crítico. Sin un canal conectado, el agente no puede operar.

* **Paso 2: Define la Personalidad - Configura tu Agente**
    * **Acción del Usuario:** El usuario accederá a un formulario en la página `/config` donde definirá los aspectos clave de la personalidad de su agente:
        * **Nombre del Agente:** El nombre que el bot usará para presentarse.
        * **Producto/Servicio:** Una descripción clara de lo que el agente está vendiendo o promocionando.
        * **Prompt del Sistema:** Instrucciones detalladas sobre su tono, estilo, objetivos y restricciones.
    * **Verificación:** El sistema guardará la configuración y confirmará al usuario.

* **Paso 3: Dota de Conocimiento a tu Agente**
    * **Acción del Usuario:** Se redirigirá al usuario a la página `/knowledge`. Aquí podrá subir los documentos (PDF, TXT, etc.) que formarán la base de conocimiento del agente.
    * **Interfaz:** Un componente de carga de archivos simple e intuitivo que permita arrastrar y soltar o seleccionar archivos.
    * **Verificación:** Una vez que el worker de embeddings procese los archivos, estos aparecerán en una lista de "Documentos Activos". Se recomienda subir al menos un documento para completar el paso.

* **Paso 4: ¡Todo Listo! - Activa y Prueba tu Agente**
    * **Acción del Usuario:** Un botón final para "Activar Agente". Al hacer clic, el sistema cambiará el estado del agente a "Activo" en la base de datos.
    * **Sugerencia de Prueba:** La interfaz mostrará una sugerencia clara: "¡Tu agente ya está activo! Envía un mensaje de WhatsApp al número conectado para iniciar tu primera conversación."
    * **Verificación:** El checklist de onboarding se marcará como completado y el usuario será redirigido al dashboard principal (`/dashboard/home`), donde podrá empezar a ver las métricas de las conversaciones entrantes.

## **Principios Guía**

* **Calidad de Producción:** Todo desarrollo se orientará a soluciones robustas, escalables y listas para producción desde el primer día. No habrá "MVPs".
* **Excelencia en Ingeniería:** Se priorizará la construcción de un sistema correcto y mantenible a largo plazo, evitando atajos que generen deuda técnica.
* **Empoderamiento del Usuario:** El objetivo final es abstraer toda la complejidad del backend para ofrecer una experiencia de usuario final simple, potente y controlable a través del dashboard.
