AGENT.MD: Constitución del Proyecto y Directiva de Refactorización Autónoma
Hola Jules.
Este documento es tu directiva principal e inmutable. Vas a realizar una refactorización completa y autónoma de este repositorio. El objetivo es alinear la base de código existente con la arquitectura y los principios definidos en esta Constitución.
Tu tarea no es simplemente arreglar o añadir, sino reestructurar, mover, eliminar y reescribir código para que se adhiera perfectamente a este manifiesto. Este AGENT.md es tu única fuente de verdad. El éxito de tu misión se medirá por cuán fielmente el código final refleja estas reglas. No pidas aclaraciones; las ambigüedades deben resolverse aplicando el principio de menor complejidad y la filosofía de "Clean Architecture".
Tu Misión: Refactorización Autónoma Completa.
1. Arquitectura de Destino: El Manifiesto
La arquitectura actual debe ser demolida y reconstruida para seguir este plano.
 * backend (Python/FastAPI) - El Núcleo Limpio:
   * Ubicación: /backend
   * Principio No Negociable: Aplicarás una Arquitectura Limpia (Hexagonal).
     * Crea un directorio backend/app/core que contendrá la lógica de negocio pura (entidades, casos de uso). Este código NO DEBE importar FastAPI, Pydantic, ni ninguna librería de base de datos. Será puro Python.
     * Los endpoints de FastAPI en backend/app/api actuarán como "adaptadores de entrada". Su única función es recibir peticiones HTTP, validarlas usando Pydantic, llamar a los casos de uso del núcleo y devolver la respuesta.
     * La interacción con Supabase será un "adaptador de salida". Crea un directorio backend/app/infrastructure o backend/app/adapters/persistence donde residirá todo el código que interactúa con la base de datos.
 * frontend (Next.js/TypeScript) - El Dashboard Centrado en el Usuario:
   * Ubicación: /frontend
   * Principio No Negociable: Adopción estricta del App Router de Next.js.
     * Migra cualquier componente de página del antiguo pages router si existiera.
     * Prioriza Server Components para todo. Solo usa el pragma "use client" cuando sea absolutamente indispensable (hooks de estado, eventos de usuario).
     * Cero lógica de negocio. El frontend es una capa de presentación. Toda la lógica de negocio, cálculos y decisiones se realizan en el backend y se consumen vía API.
 * proxy (Nginx):
   * Ubicación: /nginx
   * Confirma que su única responsabilidad sea el enrutamiento basado en prefijos (/api/ al backend, el resto al frontend) y la terminación SSL en producción.
Bases de Datos y Almacenamiento (Validación):
 * Supabase (Postgres): Verifica que se use para datos estructurados y relacionales. Valida que la seguridad a nivel de fila (RLS) esté activada en todas las tablas que contienen datos de clientes.
 * Cloudflare R2: Confirma que todos los archivos binarios (PDFs, audios, etc.) no estén en la base de datos. El código debe subirlos a R2 y la base de datos solo debe almacenar la URL o el identificador del objeto.
2. Estructura de Directorios de Destino
Refactoriza la estructura de archivos existente para que coincida exactamente con esta. Elimina cualquier archivo o directorio que no encaje en este esquema.
/
├── .env.example
├── AGENT.md            # Este archivo.
├── docker-compose.yml
├── README.md           # Actualízalo para reflejar la nueva arquitectura.
│
├── backend/
│   ├── app/
│   │   ├── api/        # Endpoints (Adaptadores de entrada).
│   │   ├── core/
│   │   │   ├── use_cases/
│   │   │   └── entities/
│   │   ├── infrastructure/ # Adaptadores de salida (DB, APIs externas).
│   │   ├── models/     # Solo modelos Pydantic para la capa de API.
│   │   └── main.py
│   ├── tests/          # Reestructura las pruebas para reflejar la nueva arquitectura.
│   ├── Dockerfile      # Optimízalo con builds multi-etapa.
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/        # Rutas y páginas (Server Components).
│   │   ├── components/ # Componentes UI reutilizables (Shadcn/ui).
│   │   ├── lib/        # Utilidades, cliente Supabase.
│   │   └── styles/
│   ├── tests/
│   ├── Dockerfile      # Optimízalo con builds multi-etapa.
│   ├── package.json
│   └── tsconfig.json
│
└── nginx/
    ├── nginx.conf
    └── Dockerfile

3. Comandos de Verificación y Validación
Estos son los comandos que DEBES ejecutar para validar cada etapa de tu refactorización. Un paso no está completo hasta que todos los comandos relevantes pasen sin errores.
3.1. Entorno Global (Docker)
 * Levantar el sistema: docker-compose up --build -d
 * Acceder a un servicio: docker-compose exec <backend|frontend> bash
3.2. Backend (Python)
 * Instalar/actualizar dependencias: pip install -r requirements.txt
 * Verificación de Calidad de Código (OBLIGATORIO):
   ruff format . && ruff check . --fix

 * Ejecución de Pruebas (OBLIGATORIO):
   pytest

3.3. Frontend (TypeScript)
 * Instalar/actualizar dependencias: npm install
 * Verificación de Calidad de Código (OBLIGATORIO):
   npm run lint

 * Ejecución de Pruebas (OBLIGATORIO):
   npm run test:ci && npx playwright test

4. Estilo de Código y Convenciones (Reglas de Refactorización)
Revisa cada línea de código existente y reescríbela si no cumple con estas reglas.
4.1. Backend (Python/FastAPI)
 * Type Hinting Estricto: No debe quedar ninguna función o variable sin su tipo definido.
 * Inyección de Dependencias: Usa Depends de FastAPI para inyectar las dependencias (como los adaptadores de la base de datos) en la capa de la API, que luego las pasará a los casos de uso del núcleo.
 * Inmutabilidad: Prefiere estructuras de datos inmutables donde sea posible.
4.2. Frontend (TypeScript/Next.js)
 * Cero any: Elimina todas las instancias del tipo any. Define interfaces y tipos estrictos para todo.
 * Hooks Personalizados: Encapsula la lógica de cliente compleja en hooks personalizados (use...).
 * Manejo de Estado: Utiliza Zustand para el estado global de la aplicación. Elimina cualquier otra solución de manejo de estado que pueda existir.
5. Directrices de Pruebas (Acción Requerida)
Tu tarea incluye la refactorización del conjunto de pruebas.
 * Cobertura: Donde no existan pruebas para una funcionalidad crítica, escríbelas.
 * Mocks: Asegúrate de que todas las pruebas unitarias y de integración hagan mock de las llamadas a redes externas.
 * Pruebas E2E (Playwright): Asegúrate de que cubran los flujos de usuario más críticos: registro, login, creación de un agente, interacción de chat.
6. Seguridad (Auditoría y Corrección)
Audita activamente el código en busca de violaciones de seguridad y corrígelas.
 * Secretos: Busca cualquier clave de API o secreto hardcodeado y reemplázalo con una carga desde variables de entorno.
 * Consultas a la DB: Revisa cada consulta a la base de datos y asegúrate de que esté parametrizada para prevenir inyecciones SQL y que respete la lógica de RLS.
 * Dependencias: Actualiza todas las dependencias a sus últimas versiones estables para mitigar vulnerabilidades conocidas.
7. Flujo de Trabajo (Tu Proceso Autónomo)
 * Planificación: Antes de escribir código, formula un plan detallado basado en este documento.
 * Ejecución Incremental: Procede por módulos. Refactoriza un componente, asegúrate de que todas las pruebas pasen, y luego pasa al siguiente.
 * Commits: Usa Conventional Commits para cada cambio significativo. refactor(core): implement clean architecture for aiRouter.
 * Pull Request Final: Al completar toda la refactorización, crea un único Pull Request contra main con un resumen detallado de los cambios masivos realizados, referenciando esta directiva como la justificación.
