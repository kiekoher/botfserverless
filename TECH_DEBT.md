# Technical Debt Log

This document tracks known technical debt items that have been consciously accepted to prioritize stability or speed but must be addressed in the future.

---

## 1. Upgrade `whatsapp-web.js` Dependency

-   **Issue Date:** 2025-08-26
-   **Component:** `services/whatsapp-gateway`
-   **Priority:** Medium

### Description

The `npm audit` process detected high-severity vulnerabilities in dependencies of the `whatsapp-web.js` library (`tar-fs` and `ws`). These dependencies are part of an old version of `puppeteer` that `whatsapp-web.js` relies on.

### Risk Assessment

The immediate risk is assessed as **LOW**.
-   The **Path Traversal** vulnerability in `tar-fs` is not exploitable as the application does not process `.tar` files.
-   The **Denial of Service** vulnerability in `ws` is not exploitable in our architecture because the gateway is not publicly exposed and only connects to official WhatsApp servers.

A detailed analysis is available in `VULNERABILITY_REPORT.md`.

### Resolution Plan

The vulnerabilities should be resolved by upgrading to a stable **2.x version** of `whatsapp-web.js` as soon as one becomes available. This was postponed to avoid introducing breaking changes before the initial launch. This task should be revisited during the next development cycle.
