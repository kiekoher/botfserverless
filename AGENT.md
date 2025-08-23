En el vertiginoso mundo del desarrollo de software, la llegada de asistentes de codificación basados en inteligencia artificial (IA) ha marcado un antes y un después. Herramientas como **Codex de OpenAI** y **Jules de Google** ya no son meros prototipos, sino agentes autónomos capaces de comprender, modificar y contribuir a bases de código complejas [1][2]. Sin embargo, para que estos agentes operen con eficacia, necesitan algo fundamental: contexto. Deben comprender la arquitectura de un proyecto, sus convenciones de estilo, cómo ejecutar pruebas y qué comandos de compilación utilizar. Históricamente, esta información ha estado dispersa en la mente de los desarrolladores o en múltiples archivos de configuración específicos para cada herramienta, creando un ecosistema fragmentado y caótico [3].

Para resolver este problema, ha surgido un nuevo estándar: el archivo `AGENT.md`. Este documento, escrito en formato Markdown, actúa como un manual de instrucciones universal para los agentes de IA, proporcionándoles una fuente de verdad única y centralizada sobre cómo interactuar con un proyecto de software. Es, en esencia, una "Piedra de Rosetta" que traduce las complejidades y matices de un repositorio de código a un lenguaje que los agentes de IA pueden entender y utilizar para escribir mejor código, corregir errores y añadir nuevas funcionalidades de manera coherente y segura [3][4].

### ¿Qué es `AGENT.md`? El Manifiesto para Agentes de IA

`AGENT.md` es un archivo de configuración y documentación diseñado para ser colocado en el directorio raíz de un proyecto de software [3]. Su propósito principal es servir como una guía completa para cualquier herramienta de codificación "agéntica", es decir, cualquier IA diseñada para realizar tareas de desarrollo de software de forma autónoma. La iniciativa, impulsada por equipos como el de Amp en Sourcegraph, busca unificar la plétora de archivos de configuración específicos que han surgido con cada nueva herramienta de IA (como `.cursorrules`, `.clinerules`, `CLAUDE.md`, etc.) en un único estándar abierto y neutral [3].

La filosofía detrás de `AGENT.md` es simple pero poderosa: **un archivo, cualquier agente** [3]. Al estandarizar la forma en que los proyectos comunican sus directrices, se eliminan las barreras para la adopción de nuevas herramientas de IA y se asegura que el código generado por ellas sea consistente, de alta calidad y se alinee con las prácticas específicas del equipo de desarrollo [4].

El formato elegido, Markdown (`.md`), es deliberado. Es legible por humanos, lo que facilita su creación y mantenimiento por parte de los desarrolladores, y al mismo tiempo es fácilmente analizable (parseable) por las máquinas, permitiendo que los agentes de IA extraigan la información estructurada que necesitan [3].

### La Especificación de `AGENT.md`: Estructura y Contenido

Para que `AGENT.md` sea efectivo, sigue una especificación que define su estructura, contenido y comportamiento. Esta especificación asegura que las herramientas de IA puedan encontrar y procesar la información de manera predecible [3].

#### Ubicación y Jerarquía

*   **Archivo Raíz**: El `AGENT.md` principal debe ubicarse en el directorio raíz del proyecto para proporcionar una guía general [3].
*   **Estructura Jerárquica**: La especificación soporta la existencia de múltiples archivos `AGENT.md`. Se pueden colocar archivos adicionales en subdirectorios para proporcionar directrices más específicas para subsistemas o componentes concretos del proyecto. Además, un desarrollador puede tener un archivo `AGENT.md` global en su configuración de usuario (por ejemplo, en `~/.config/AGENT.md`) para definir preferencias personales. Cuando existen múltiples archivos, las herramientas deben fusionar las configuraciones, dando siempre precedencia a la más específica (el archivo del subdirectorio anula al del raíz, que a su vez anula al global) [3].

#### Secciones Fundamentales de un Archivo `AGENT.md`

Un archivo `AGENT.md` bien estructurado es como la sesión de incorporación de un nuevo miembro del equipo. Debe contener toda la información clave que un desarrollador (humano o artificial) necesita para empezar a contribuir de forma productiva y segura. Las secciones recomendadas son las siguientes [3][4]:

**1. Descripción General y Arquitectura del Proyecto**
Esta sección inicial actúa como una introducción de alto nivel. Debe describir brevemente el propósito del proyecto y su arquitectura fundamental.
*   **Ejemplo**: "MyApp es una aplicación web full-stack con un frontend en TypeScript y un backend en Node.js. La funcionalidad principal reside en la carpeta `src/`, con componentes separados para el cliente (`client/`) y el servidor (`server/`)" [3].
*   **Para la IA**: Esto le da al agente un contexto inmediato sobre la tecnología utilizada y la organización conceptual del código, ayudándole a tomar decisiones más informadas.

**2. Estructura del Proyecto y Organización**
Aquí se detalla el diseño del sistema de archivos. Se debe explicar qué contiene cada directorio principal, guiando al agente sobre dónde encontrar el código fuente, las pruebas, los componentes de la interfaz de usuario, los estilos, etc.
*   **Ejemplo para Codex**:
    *   `/src`: Código fuente que OpenAI Codex debe analizar.
    *   `/components`: Componentes de React que `AGENT.md` ayuda a OpenAI Codex a entender.
    *   `/tests`: Archivos de prueba que OpenAI Codex debe mantener y extender [4].
*   **Para la IA**: Esta sección es crucial para que el agente navegue por el repositorio de manera eficiente, sepa qué archivos modificar y cuáles debe ignorar (como los activos estáticos en `/public`) [4].

**3. Comandos de Compilación, Pruebas y Desarrollo**
Esta es una de las secciones más críticas. Enumera los comandos exactos necesarios para instalar dependencias, ejecutar linters, formatear código, correr pruebas (todas o una específica), iniciar el servidor de desarrollo y compilar la aplicación para producción.
*   **Ejemplo**:
    *   Verificar tipos y linting: `pnpm check`
    *   Correr pruebas: `pnpm test --run --no-color`
    *   Iniciar servidor de desarrollo: `pnpm dev` [3].
*   **Para la IA**: Un agente autónomo necesita poder verificar su propio trabajo. Al proporcionarle estos comandos, puede ejecutar las pruebas después de realizar un cambio para asegurarse de que no ha roto nada, o ejecutar el linter para que su código se adhiera al estilo del proyecto antes de proponerlo [5].

**4. Estilo de Código y Convenciones**
Esta sección define las "reglas de la casa" para escribir código. Incluye detalles como el uso de pestañas o espacios, comillas simples o dobles, el límite de caracteres por línea, convenciones de nomenclatura (por ejemplo, `URL` vs. `Url`), y el uso de patrones de programación específicos.
*   **Ejemplo**:
    *   Usar comillas simples, sin punto y coma, comas finales.
    *   Límite de 100 caracteres por línea.
    *   En nombres CamelCase, usar "URL" (no "Url"), "API" (no "Api").
    *   NUNCA usar `@ts-expect-error` o `@ts-ignore` para suprimir errores de tipo [3].
*   **Para la IA**: Al codificar estas reglas, se instruye al agente para que genere un código que sea indistinguible del escrito por un humano del equipo, manteniendo la consistencia y la legibilidad de la base de código [4].

**5. Directrices de Pruebas**
Además de los comandos para ejecutar pruebas, esta sección detalla *cómo* se deben escribir las pruebas. Especifica los frameworks utilizados (ej. Vitest, Playwright), las bibliotecas (ej. Testing Library) y las convenciones a seguir.
*   **Ejemplo**:
    *   Usar Vitest para pruebas unitarias y Playwright para pruebas E2E.
    *   Omitir "should" de los nombres de las pruebas (ej. `it("validates input")` en lugar de `it("should validate input")`).
    *   Los archivos de prueba deben terminar en `*.test.ts` o `*.spec.ts` [3].
*   **Para la IA**: Esto permite que agentes como Jules o Codex no solo corrijan un error, sino que también escriban una prueba de regresión para él, siguiendo exactamente las mismas convenciones que el resto del equipo [1][4].

**6. Consideraciones de Seguridad**
La seguridad es primordial. Esta sección instruye al agente sobre prácticas seguras, como no incluir nunca secretos (API keys, contraseñas) en el repositorio, validar todas las entradas del usuario y seguir el principio de mínimo privilegio.
*   **Ejemplo**:
    *   Nunca cometer secretos o claves de API en el repositorio.
    *   Usar variables de entorno para datos sensibles.
    *   Validar todas las entradas del usuario tanto en el cliente como en el servidor [3].
*   **Para la IA**: Esto ayuda a prevenir que el agente introduzca vulnerabilidades de seguridad comunes de forma accidental mientras genera código.

**7. Flujo de Trabajo con Git y Pull Requests**
Define el proceso para contribuir con código, incluyendo las verificaciones que se deben realizar antes de un `commit` y las directrices para crear Pull Requests (PRs).
*   **Ejemplo para Codex**:
    1.  Incluir una descripción clara de los cambios.
    2.  Referenciar cualquier issue relacionado.
    3.  Asegurarse de que todas las pruebas pasan para el código generado [4].
*   **Para la IA**: Esto asegura que las contribuciones del agente se integren sin problemas en el flujo de trabajo del equipo, facilitando la revisión por parte de los desarrolladores humanos.

### `AGENT.MD` en Acción: El Caso de OpenAI Codex

OpenAI Codex, el modelo de IA que impulsa a GitHub Copilot, fue uno de los primeros sistemas para los que se conceptualizó la idea de un archivo de guía [2][4]. Para Codex, `AGENTS.MD` (a veces nombrado `AGENTS.MD` en la documentación inicial) actúa como su principal fuente de conocimiento contextual sobre un proyecto [6][7].

Cuando Codex interactúa con un repositorio que contiene este archivo, lo analiza para guiar su proceso de generación de código. Los beneficios son tangibles [4]:
*   **Mayor Calidad de Código**: Al conocer las convenciones de estilo, los patrones de arquitectura y las mejores prácticas del proyecto, Codex genera un código que requiere menos refactorización y revisiones manuales [4].
*   **Consistencia**: Asegura que las nuevas funciones o correcciones generadas por la IA se integren perfectamente con el código existente, manteniendo una base de código coherente .
*   **Reducción del Tiempo de Desarrollo**: Codex puede entender la arquitectura del proyecto casi instantáneamente, eliminando la curva de aprendizaje que incluso un desarrollador humano tendría y volviéndose productivo desde el primer momento .
*   **Generación de Pruebas Relevantes**: Al tener claras las directrices y los comandos de prueba, Codex no solo escribe código funcional, sino también las pruebas unitarias o de integración correspondientes, mejorando la robustez general del software [4][5].

El archivo `AGENT.MD` se convierte, de hecho, en un puente de comunicación entre el equipo de desarrollo y la IA, traduciendo requisitos implícitos y explícitos en instrucciones directas para el agente [4].

### `AGENT.MD` en Acción: El Caso de Jules de Google

Jules es un asistente de codificación agéntico y asíncrono de Google, impulsado por el avanzado modelo Gemini 2.5 Pro [1]. A diferencia de los asistentes que operan en tiempo real, Jules trabaja en segundo plano. Clona el repositorio en una máquina virtual segura en la nube de Google, analiza el contexto completo del proyecto y realiza tareas complejas como escribir pruebas, corregir errores, actualizar dependencias o construir nuevas funcionalidades [1].

La documentación oficial de Jules confirma explícitamente su soporte para este estándar: "**Jules ahora busca automáticamente un archivo llamado `AGENTS.MD` en la raíz de su repositorio**" [8].

Para Jules, el archivo `AGENT.MD` es fundamental para su fase de "planificación". Antes de realizar cualquier cambio en el código, Jules presenta al desarrollador un plan detallado de lo que pretende hacer y por qué. El contenido del `AGENT.MD` alimenta directamente este proceso de razonamiento [1].
*   **Mejora de la Planificación**: Al leer el `AGENT.MD`, Jules obtiene una comprensión más profunda del código y puede generar "planes y terminaciones más relevantes" [8].
*   **Ejecución Autónoma**: Las secciones sobre comandos de compilación y prueba son vitales para Jules. Al operar en una VM en la nube, utiliza estos comandos para verificar que sus cambios son correctos y que todas las pruebas pasan antes de presentar el resultado final al desarrollador [1].
*   **Integración con el Flujo de Trabajo**: Al igual que con Codex, las directrices sobre Git y PRs en el `AGENT.MD` ayudan a Jules a empaquetar sus contribuciones de una manera que se alinea con las prácticas del equipo.

La recomendación en la documentación de Jules es clara: "Mantenga `AGENTS.MD` actualizado. Ayuda a Jules y a sus compañeros de equipo a trabajar con su repositorio de manera más efectiva" [8]. Esto subraya el doble beneficio del archivo: no solo guía a los agentes de IA, sino que también sirve como una excelente documentación viva para los desarrolladores humanos.

### Hacia un Ecosistema Unificado

La verdadera visión de `AGENT.MD` va más allá de una sola herramienta. El objetivo es crear un estándar universal que libere a los desarrolladores de la carga de mantener múltiples archivos de configuración. La especificación de `AGENT.MD` incluye una guía de migración que utiliza enlaces simbólicos para que las herramientas heredadas puedan seguir funcionando mientras leen desde el nuevo archivo unificado `AGENT.MD` [3].

Por ejemplo, para migrar desde un archivo `.cursorrules` de la herramienta Cursor, el comando sería:
`mv .cursorrules AGENT.MD && ln -s AGENT.MD .cursorrules`

Este comando renombra el archivo de configuración antiguo a `AGENT.MD` y luego crea un enlace simbólico con el nombre antiguo que apunta al nuevo archivo. De este modo, la herramienta antigua sigue encontrando el archivo que busca, pero el contenido ahora está centralizado en el estándar `AGENT.MD` [3]. La especificación proporciona comandos similares para herramientas como Claude Code, Gemini CLI, OpenAI Codex, Replit y otras [3].

### Conclusión: Un Pilar para la Colaboración Humano-IA

El archivo `AGENT.MD` representa un paso maduro y necesario en la evolución del desarrollo de software asistido por IA. Transforma la forma en que los humanos colaboran con los agentes de codificación, pasando de dar instrucciones vagas en un prompt a proporcionar un manual de operaciones rico, estructurado y contextualizado.

Para los equipos de desarrollo, adoptar el estándar `AGENT.MD` ofrece una triple victoria:
1.  **Potencia a los Agentes de IA**: Permite que herramientas como Codex y Jules trabajen de manera más inteligente, rápida y segura, generando código de mayor calidad que se alinea con los estándares del proyecto [4][1].
2.  **Mejora la Documentación Humana**: Obliga a los equipos a documentar explícitamente sus procesos y convenciones, lo que beneficia la incorporación de nuevos desarrolladores humanos y la mantenibilidad a largo plazo del proyecto [8].
3.  **Prepara para el Futuro**: Al adoptar un estándar abierto y universal, los equipos se aseguran de que su base de código esté lista para la próxima generación de herramientas de IA sin necesidad de reconfiguraciones masivas [3][9].

En resumen, `AGENT.MD` es mucho más que un simple archivo de configuración. Es un manifiesto que declara cómo un proyecto de software debe ser tratado, un contrato de colaboración entre desarrolladores humanos y sus contrapartes de silicio. A medida que los agentes de IA se vuelvan cada vez más centrales en el ciclo de vida del desarrollo de software, este "manual universal" se consolidará como un pilar fundamental para una colaboración efectiva, consistente y verdaderamente poderosa.

Citas:
[1] Jules: Google's autonomous AI coding agent https://blog.google/technology/google-labs/jules/
[2] Codex - OpenAI API https://platform.openai.com/docs/codex/overview
[3] AGENT.md: The Universal Agent Configuration File - Amp https://ampcode.com/agent.md
[4] Agents.md Guide for OpenAI Codex - Enhance AI Coding https://agentsmd.net
[5] This is How I Use Openai Codex Swe Agent | Instructa Courses https://www.instructa.ai/blog/this-is-how-i-use-openai-codex-swe-agent
[6] AGENTS.md SPEC for OpenAI Codex - GitHub Gist https://gist.github.com/dpaluy/cc42d59243b0999c1b3f9cf60dfd3be6
[7] Mastering Codex Agent Configuration Files: A Complete Guide https://www.linkedin.com/pulse/mastering-codex-agent-configuration-files-complete-lozovsky-mba-zyh8c
[8] Getting started https://jules.google/docs
[9] AGENTS.md standardisation for agentic coding systems https://sgryphon.gamertheory.net/2025/07/agents-md-standardisation-for-agentic-coding-systems/
[10] AGENT.md | DoltHub Blog https://www.dolthub.com/blog/2025-08-05-agent-dot-md/

---

## Guía Específica del Proyecto EVA

Esta sección proporciona el contexto y las instrucciones específicas para el repositorio de EVA, siguiendo el estándar `AGENT.md`.

### 1. Descripción General y Arquitectura del Proyecto

EVA es una plataforma SaaS multi-tenant para desplegar agentes de ventas impulsados por inteligencia artificial. El sistema sigue una arquitectura de microservicios y está completamente orquestado por Docker Compose para un despliegue en un único servidor.

*   **`frontend` (Next.js):** Panel de control del usuario.
*   **`main-api` (Python/FastAPI):** Núcleo de la aplicación, maneja la lógica de negocio.
*   **`whatsapp-gateway` (Node.js):** Punto de entrada para mensajes de WhatsApp. **Nota:** Este servicio utiliza la librería `whatsapp-web.js`, que no es una API oficial de WhatsApp. Su uso ha sido evaluado y aceptado como un riesgo de negocio para la fase actual del proyecto.
*   **`transcription-worker` (Python):** Procesa mensajes de audio.
*   **`embedding-worker` (Python):** Procesa documentos para la base de conocimiento.
*   **`traefik` (Traefik):** Reverse proxy y gestión de SSL.
*   **`redis` (Redis):** Message broker para comunicación asíncrona.
*   **`loki` & `promtail`:** Pila de logging centralizado.
*   **`supabase` (PostgreSQL):** Base de datos y autenticación.

### 2. Estructura del Proyecto y Organización

*   `/frontend`: Contiene todo el código de la aplicación Next.js.
*   `/services`: Contiene los Dockerfiles y el código fuente para todos los microservicios del backend.
    *   `/services/main-api`: El servicio más importante, con la lógica de negocio principal en `app/`.
    *   `/services/whatsapp-gateway`: El puente de Node.js con WhatsApp.
    *   `/services/*-worker`: Los diferentes workers asíncronos.
*   `/supabase`: Contiene las migraciones de la base de datos.
*   `docker-compose.prod.yml`: Define la arquitectura completa de producción.
*   `AGENT.md`: Este archivo.

### 3. Comandos de Compilación, Pruebas y Desarrollo

La única fuente de verdad para la ejecución es `docker-compose.prod.yml`.

*   **Instalar dependencias:** Las dependencias se gestionan dentro de las imágenes de Docker. No es necesario instalarlas manualmente en el host.
*   **Iniciar el entorno completo:**
    ```bash
    docker-compose -f docker-compose.prod.yml up --build -d
    ```
*   **Ver logs de un servicio:**
    ```bash
    docker-compose -f docker-compose.prod.yml logs -f <nombre-del-servicio>
    # Ejemplo: docker-compose -f docker-compose.prod.yml logs -f whatsapp-gateway
    ```
*   **Ejecutar pruebas de backend (`main-api`):**
    ```bash
    docker-compose -f docker-compose.prod.yml exec main-api pytest
    ```
*   **Ejecutar pruebas de frontend:**
    ```bash
    docker-compose -f docker-compose.prod.yml exec frontend npm test
    ```

### 4. Estilo de Código y Convenciones

*   **Backend (Python):** El estilo de código es gestionado por `ruff`. La configuración se encuentra en el archivo `pyproject.toml` (a ser creado o verificado).
*   **Frontend (TypeScript/JavaScript):** El estilo de código es gestionado por `eslint`. La configuración se encuentra en `.eslintrc.json`. Se deben seguir las reglas de React y Next.js.
*   **General:** Seguir las convenciones existentes en el código base.

### 5. Directrices de Pruebas

*   **Backend:** Las pruebas unitarias y de integración se escriben con `pytest` y se encuentran en el directorio `tests/` de cada servicio.
*   **Frontend:** Las pruebas de componentes se escriben con `jest` y `@testing-library/react`. Se encuentran en los directorios `__tests__` dentro de la estructura de la aplicación.

### 6. Consideraciones de Seguridad

*   **Nunca cometer secretos:** Todas las claves de API, contraseñas y otros datos sensibles deben gestionarse a través de GitHub Secrets y pasarse al entorno de producción como variables de entorno en el archivo `.env.prod`, que es generado por el pipeline de CI/CD y nunca debe ser comiteado.
*   **Base de Datos:** La base de datos de Supabase está protegida con Row Level Security (RLS) para asegurar el aislamiento de los datos de los tenants.

### 7. Flujo de Trabajo con Git y Pull Requests

*   El despliegue a producción es automático al hacer push a la rama `main`.
*   El pipeline de CI/CD (definido en `.github/workflows/deploy.yml`) debe pasar todas las pruebas y lints antes de que se permita el despliegue.
*   Todo cambio debe hacerse en una rama de feature y ser fusionado a `main` a través de un Pull Request.
