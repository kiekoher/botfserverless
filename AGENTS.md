# Guía para Agentes de IA

Este repositorio está preparado para colaborar con agentes de codificación como **Codex** de OpenAI y **Jules** de Google. Lee este archivo antes de hacer cambios para entender la arquitectura, comandos y normas del proyecto.

## 1. Descripción general del proyecto

EVA es una plataforma SaaS multi‑tenant para desplegar agentes de ventas impulsados por IA. Sigue una arquitectura de microservicios orquestada con Docker Compose.

Servicios principales:

- **frontend**: panel de control en Next.js.
- **services/main-api**: núcleo de negocio en Python/FastAPI.
- **services/whatsapp-gateway**: puente Node.js para WhatsApp (usa `whatsapp-web.js`).
- **services/transcription-worker**: worker Python que transcribe audio.
- **services/embedding-worker**: worker Python que genera embeddings.
- **traefik**: proxy inverso y SSL.
- **redis**: message broker.
- **loki/promtail**: logging centralizado.
- **supabase**: PostgreSQL y autenticación.

## 2. Estructura del repositorio

```
frontend/               # aplicación Next.js
services/               # microservicios backend
  main-api/             # lógica de negocio principal
  whatsapp-gateway/     # integración con WhatsApp
  transcription-worker/ # transcribe mensajes de audio
  embedding-worker/     # procesa documentos
supabase/               # migraciones de base de datos
alertmanager/, grafana/, prometheus/, promtail/  # monitoreo y observabilidad
docker-compose.prod.yml # arquitectura de producción
```

## 3. Comandos de desarrollo y pruebas

La fuente de verdad es `docker-compose.prod.yml`.

```bash
# Iniciar todo el entorno
docker-compose -f docker-compose.prod.yml up --build -d

# Ver logs de un servicio
docker-compose -f docker-compose.prod.yml logs -f <servicio>
# Ejemplo: docker-compose -f docker-compose.prod.yml logs -f whatsapp-gateway

# Pruebas del backend
docker-compose -f docker-compose.prod.yml exec main-api pytest

# Pruebas del frontend
docker-compose -f docker-compose.prod.yml exec frontend npm test
```

Las dependencias se instalan dentro de las imágenes de Docker; no es necesario instalarlas en el host.

## 4. Estilo de código

- **Python**: usar `ruff` (ver configuración en `pyproject.toml`).
- **TypeScript/JavaScript**: usar `eslint` según `.eslintrc.*` del proyecto.
- Mantén el estilo existente y evita introducir nuevas convenciones sin alinearlas con el equipo.

## 5. Directrices de pruebas

- Las pruebas de backend usan `pytest` y se encuentran en `tests/` dentro de cada servicio.
- El frontend usa `jest` y `@testing-library/react`; las pruebas viven en directorios `__tests__`.
- Cada nueva funcionalidad debe incluir pruebas unitarias o de integración.

## 6. Seguridad

- **Nunca** incluyas secretos en el repositorio. Usa variables de entorno; el archivo `.env.prod` se genera en el pipeline de CI/CD y no debe comitearse.
- Supabase utiliza Row Level Security para aislar tenants; respeta este aislamiento en la lógica de negocio.

## 7. Flujo de trabajo con Git y Pull Requests

- Trabaja en ramas de feature. No comites directamente a `main`.
- Asegúrate de que las pruebas y linters pasen antes de crear un PR.
- Los PR deben describir claramente los cambios y referenciar issues relacionados.
- Los pushes a `main` despliegan automáticamente a producción via GitHub Actions (`.github/workflows/deploy.yml`).

---
Mantén este archivo actualizado para ayudar tanto a agentes de IA como a desarrolladores humanos.
