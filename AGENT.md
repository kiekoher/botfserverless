# Guía para Agentes de IA y Desarrolladores

**Versión:** 2.0 (Actualizada)

Este documento proporciona una visión general de la arquitectura del proyecto y los comandos esenciales para el desarrollo local.

**IMPORTANTE:** Para cualquier tarea relacionada con la configuración de producción, despliegue, gestión de secretos o mantenimiento, consulta la guía maestra:
### ➡️ [**Guía Maestra de Despliegue a Producción (`DEPLOYMENT_GUIDE.md`)**](./DEPLOYMENT_GUIDE.md)

---

## 1. Arquitectura General

EVA es una plataforma SaaS multi‑tenant para desplegar agentes de ventas impulsados por IA. Sigue una **arquitectura serverless híbrida** para máxima escalabilidad y mínimo mantenimiento.

*   **Frontend**: Panel de control en Next.js, desplegado en **Vercel**.
*   **API**: Lógica de negocio principal en Python/FastAPI, ejecutándose como **Vercel Serverless Functions**.
*   **Workers Asíncronos**: Workers de TypeScript en **Cloudflare** para tareas como transcripción y generación de embeddings.
*   **Base de Datos y Autenticación**: **Supabase Cloud** (PostgreSQL).
*   **Almacenamiento de Archivos**: **Cloudflare R2**.
*   **Gateway de WhatsApp**: Servicio Node.js en un **contenedor Docker auto-alojado** en un servidor Ubuntu.

---

## 2. Desarrollo y Pruebas Locales

Las pruebas y el desarrollo local se gestionan con las herramientas CLI de cada plataforma.

### Comandos de Desarrollo
```bash
# Iniciar el entorno de desarrollo local de Vercel (frontend + API)
# Desde el directorio raíz del proyecto:
vercel dev

# Iniciar el entorno de desarrollo de Cloudflare Workers
# Desde el directorio /workers:
npx wrangler dev
```

### Comandos de Prueba
```bash
# Pruebas de la API (Python)
# Desde el directorio raíz del proyecto:
pytest api/

# Pruebas del Frontend (Next.js)
# Desde el directorio /frontend:
npm test

# Pruebas del Gateway de WhatsApp (Node.js)
# Desde el directorio /services/whatsapp-gateway:
npm test
```

---

## 3. Estilo de Código

*   **Python**: Se utiliza `ruff`.
*   **TypeScript/JavaScript**: Se utiliza `eslint` y `prettier`.

Por favor, mantén el estilo de código existente al contribuir.
