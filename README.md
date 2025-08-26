# EVA: Plataforma Serverless de Agentes de Ventas con IA

![EVA Banner](https://user-images.githubusercontent.com/12345/eva-banner.png) <!-- Placeholder for a nice banner -->

**EVA** es una plataforma SaaS multi-tenant para desplegar agentes de ventas conversacionales impulsados por inteligencia artificial. El sistema está diseñado con una arquitectura híbrida y serverless-first para ofrecer alta escalabilidad, mínimo mantenimiento y un ciclo de despliegue automatizado.

## Arquitectura de un Vistazo

- **Frontend:** Next.js (desplegado en Vercel)
- **API de Negocio:** Python/FastAPI (desplegada como Vercel Serverless Functions)
- **Workers Asíncronos:** TypeScript (desplegados en Cloudflare Workers para transcripción, embeddings, etc.)
- **Gateway de WhatsApp:** Node.js (desplegado como un contenedor Docker auto-alojado)
- **Infraestructura de Datos:** Supabase (Base de Datos, Auth) y Cloudflare R2 (Almacenamiento de Archivos).

---

## 🚀 Guía de Despliegue y Desarrollo

Toda la información técnica, guías de configuración, procedimientos de despliegue y detalles de la arquitectura han sido consolidados en un único documento maestro.

### ➡️ [**Lee la Guía de Despliegue Completa (`DEPLOYMENT_GUIDE.md`)**](./DEPLOYMENT_GUIDE.md)

Este documento contiene todo lo que necesitas saber para configurar, desplegar y mantener la plataforma EVA, incluyendo:
- Configuración de servicios en la nube (Supabase, Cloudflare, Google Cloud).
- Gestión de secretos con Doppler.
- Procedimientos de despliegue automatizado con GitHub Actions.
- Guías de hardening de seguridad.
- Monitorización y observabilidad.

---

## 🧪 Pruebas

Para ejecutar las pruebas de cada componente, consulta las instrucciones en sus respectivos directorios:
- `api/`: Pruebas de la API de FastAPI.
- `frontend/`: Pruebas del panel de Next.js.
- `services/whatsapp-gateway/`: Pruebas del gateway.

---

## 📄 Licencia

Este proyecto es software propietario. Todos los derechos están reservados.
