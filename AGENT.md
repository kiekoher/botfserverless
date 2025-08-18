AGENT.MD: Manual de Operaciones para Jules
Hola Jules. Este documento es tu guía principal y la fuente de verdad para interactuar con este repositorio. Has sido incorporado a nuestro equipo como un compañero de equipo asíncrono y autónomo. Tu éxito depende de tu capacidad para comprender y seguir meticulosamente las directrices aquí contenidas.
Antes de realizar cualquier cambio, tu primer paso es siempre analizar este archivo en su totalidad. Utilízalo para formar tu "plan de acción", que presentarás para su revisión. La calidad de tu plan y del código resultante está directamente ligada a tu adhesión a este manual.
1. Descripción General y Arquitectura del Proyecto
Este proyecto es una plataforma de agentes conversacionales multi-tenant, diseñada para ser robusta, escalable y segura. La arquitectura está completamente dockerizada para unificar los entornos de desarrollo y producción.
La arquitectura se compone de tres servicios principales orquestados por docker-compose.yml:
 * backend (Python/FastAPI): El Cerebro - "El Santo Grial"
   * Ubicación: /backend
   * Descripción: Es una API de Python que utiliza el framework FastAPI. Implementa toda la lógica de IA, incluyendo el componente central aiRouter. Este orquestador direcciona las solicitudes al motor de IA especializado correcto (Gemini para chat en tiempo real, DeepSeek para análisis, OpenAI para embeddings, etc.). Es responsable de toda la lógica de negocio y la comunicación con la base de datos.
   * NO contiene lógica de frontend.
 * frontend (Next.js/TypeScript): El Dashboard de Control
   * Ubicación: /frontend
   * Descripción: Es una aplicación Next.js (App Router) escrita en TypeScript. Proporciona la interfaz de usuario para que los clientes gestionen sus agentes de IA, configuren bases de conocimiento, vean conversaciones y controlen la configuración de seguridad. Se comunica con el backend a través de una API RESTful.
   * NO contiene lógica de backend ni acceso directo a la base de datos, excepto para la autenticación del cliente.
 * proxy (Nginx): La Puerta de Entrada
   * Ubicación: /nginx
   * Descripción: Es un servidor Nginx que actúa como un reverse proxy. Dirige el tráfico de la API (ej. /api/v1/...) al servicio backend y todo el resto del tráfico al servicio frontend. En producción, también se encarga de la terminación SSL (HTTPS).
Base de Datos y Almacenamiento:
 * Supabase (Cloud): Se utiliza como nuestra base de datos PostgreSQL y proveedor de autenticación. La multi-tenancy se implementa a nivel de base de datos mediante Row Level Security (RLS).
 * Cloudflare R2: Se utiliza para el almacenamiento de objetos (archivos grandes como PDFs, audios). La base de datos solo contiene metadatos y punteros a los objetos en R2.
2. Estructura del Proyecto y Organización
Tu capacidad para navegar el repositorio es crucial. Aquí está el mapa.
/
├── .env.example        # Plantilla para variables de entorno. NUNCA cometer el .env real.
├── AGENT.md            # Este archivo. Tu fuente de verdad.
├── docker-compose.yml  # Orquesta el inicio de todos los servicios.
├── README.md           # Documentación general para desarrolladores humanos.
│
├── backend/            # Contenedor del servicio de backend (FastAPI)
│   ├── app/            # Código fuente principal de la API
│   │   ├── api/        # Endpoints/Rutas de la API (ej. chat, agentes)
│   │   ├── core/       # Lógica de negocio principal (ej. aiRouter.py)
│   │   ├── models/     # Modelos de datos Pydantic y esquemas de la DB
│   │   ├── services/   # Clientes para servicios externos (Gemini, OpenAI, Supabase)
│   │   └── main.py     # Punto de entrada de la aplicación FastAPI
│   ├── tests/          # Pruebas unitarias y de integración para el backend
│   ├── Dockerfile      # Instrucciones para construir la imagen Docker del backend
│   └── requirements.txt # Dependencias de Python
│
├── frontend/           # Contenedor del servicio de frontend (Next.js)
│   ├── src/
│   │   ├── app/        # Rutas y páginas (Next.js App Router)
│   │   ├── components/ # Componentes React reutilizables (construidos con Shadcn/ui)
│   │   ├── lib/        # Funciones de utilidad, cliente Supabase, etc.
│   │   └── styles/     # Estilos globales de CSS/Tailwind
│   ├── public/         # Activos estáticos (imágenes, fuentes)
│   ├── tests/          # Pruebas E2E (Playwright) y de componentes (Vitest)
│   ├── Dockerfile      # Instrucciones para construir la imagen Docker del frontend
│   ├── package.json    # Dependencias y scripts de Node.js
│   └── tsconfig.json   # Configuración de TypeScript
│
└── nginx/              # Contenedor del proxy Nginx
    ├── nginx.conf      # Configuración del servidor Nginx
    └── Dockerfile      # Instrucciones para construir la imagen Docker de Nginx

3. Comandos de Compilación, Pruebas y Desarrollo
Esta es la sección más crítica para tu operación autónoma. DEBES ejecutar estos comandos en tu entorno de VM para verificar tu propio trabajo antes de proponer cambios. Un PR con pruebas o linters fallidos no será aceptado.
3.1. Entorno Global (Docker)
La única forma de ejecutar el sistema es a través de Docker Compose.
 * Levantar todo el sistema:
   docker-compose up --build -d

 * Acceder a un servicio: Para ejecutar comandos específicos, accede al shell del contenedor correspondiente.
   # Para el backend
docker-compose exec backend bash
# Para el frontend
docker-compose exec frontend bash

3.2. Comandos Específicos del Backend (Python)
Ubicación para ejecutar: Dentro del contenedor backend.
 * Instalar/actualizar dependencias:
   pip install -r requirements.txt

 * Verificar formato y linting (OBLIGATORIO): Usamos Ruff. Tu código debe pasar esta verificación.
   # Formatear el código
ruff format .
# Verificar y corregir problemas de linting
ruff check . --fix

 * Ejecutar todas las pruebas (OBLIGATORIO): Usamos Pytest. El resultado debe ser 100% exitoso.
   pytest

3.3. Comandos Específicos del Frontend (TypeScript)
Ubicación para ejecutar: Dentro del contenedor frontend.
 * Instalar/actualizar dependencias:
   npm install

 * Verificar formato y linting (OBLIGATORIO): Usamos ESLint y Prettier.
   npm run lint

 * Ejecutar pruebas de componentes/unitarias (OBLIGATORIO): Usamos Vitest.
   npm run test:ci

 * Ejecutar pruebas End-to-End (OBLIGATORIO): Usamos Playwright.
   npx playwright test

4. Estilo de Código y Convenciones
La consistencia es fundamental. Tu código debe ser indistinguible del escrito por un humano del equipo.
4.1. Backend (Python/FastAPI)
 * Formato y Linting: La configuración de Ruff en pyproject.toml es la única fuente de verdad.
 * Type Hinting: TODO el código debe tener type hints de Python. El tipado estricto es obligatorio.
 * Modelos de Datos: Usa Pydantic para todos los modelos de API y validación.
 * Nomenclatura:
   * Variables y funciones: snake_case.
   * Clases: PascalCase.
 * Arquitectura: Sigue los principios de Clean Architecture. La lógica de negocio en app/core debe ser independiente del framework.
4.2. Frontend (TypeScript/Next.js)
 * Formato y Linting: Las configuraciones en .eslintrc.json y .prettierrc son la única fuente de verdad.
 * TypeScript: Usa TypeScript en modo estricto. Evita el uso de any.
 * Componentes: Usa Server Components por defecto. Solo usa "use client" cuando sea estrictamente necesario.
 * Estilos: Usa Tailwind CSS para todos los estilos.
5. Directrices de Pruebas
"Lo que no se prueba, no funciona". Cualquier nueva funcionalidad o corrección de error debe ir acompañada de pruebas. Esta es una tarea ideal para ti.
 * Backend:
   * Crea pruebas unitarias en backend/tests/unit.
   * Crea pruebas de integración en backend/tests/integration.
   * Mocks: Realiza mocks de TODAS las llamadas a APIs externas (Gemini, OpenAI, etc.).
 * Frontend:
   * Crea pruebas de componentes/unitarias (*.test.tsx) con Vitest y React Testing Library.
   * Crea pruebas End-to-End (*.spec.ts) con Playwright para simular flujos de usuario completos.
6. Consideraciones de Seguridad
La seguridad es nuestra máxima prioridad.
 * NUNCA HARDCODEAR SECRETOS: Nunca escribas claves de API, contraseñas o tokens directamente en el código. Utiliza siempre variables de entorno.
 * MULTI-TENANCY (RLS): Toda consulta a la base de datos desde el backend DEBE estar filtrada por el organization_id del usuario autenticado.
 * VALIDACIÓN DE ENTRADAS: Valida rigurosamente TODA la información que llega a la API del backend usando modelos Pydantic.
7. Flujo de Trabajo con Git y Pull Requests
Este es tu proceso para contribuir.
 * Tu Entorno: Trabajarás en una rama creada a partir de main.
 * Commits: Usa el estándar de Conventional Commits.
   * Formato: <tipo>(<ámbito>): <descripción>
   * Ejemplo: feat(api): add endpoint for agent pause
 * Pull Requests (PRs):
   * Al finalizar tu tarea, crearás un Pull Request contra la rama main.
   * Título: Claro y siguiendo el estilo de Conventional Commits.
   * Descripción: Explica QUÉ hace el PR y POR QUÉ, referenciando este archivo si es necesario para justificar tu plan.
   * Verificación: Antes de crear el PR, asegúrate de haber ejecutado y pasado todos los comandos de la sección 3.
   * Revisión Humana: Tu PR será revisado por un desarrollador humano. Estás aquí para asistir y acelerar, no para eludir la supervisión.
