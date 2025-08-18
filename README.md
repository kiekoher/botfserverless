# Crezgo AI Bot - Refactored Architecture

This project is an AI-powered chatbot for the consulting firm **Crezgo**. It has been refactored into a modern, multi-service architecture to improve scalability, maintainability, and separation of concerns, following the principles of Clean Architecture.

The system is composed of three main services orchestrated by Docker Compose:

1.  **`backend` (Python/FastAPI):** The core of the application. It handles all business logic, including intent classification, Retrieval-Augmented Generation (RAG) from a knowledge base, and interactions with external services like Google Gemini and Supabase. It exposes a REST API.
2.  **`whatsapp` (Node.js/whatsapp-web.js):** The communication layer. This service acts as an adapter, connecting to WhatsApp using `whatsapp-web.js`. It receives messages from users and forwards them to the `backend` service for processing, then sends the response back to the user. It includes anti-detection mechanisms to ensure stability.
3.  **`nginx` (Nginx):** The reverse proxy. It routes incoming requests to the appropriate service. All API calls to `/api/` are directed to the `backend` service.

---

## 🚀 Getting Started

### 1. Prerequisites

- Docker
- Docker Compose

### 2. Environment Variables

First, create a `.env` file from the example provided:

```bash
cp .env.example .env
```

Next, open the `.env` file and fill in the required values:

-   `SUPABASE_URL`: Your project's Supabase URL.
-   `SUPABASE_KEY`: Your project's Supabase service role key (this key has admin privileges).
-   `GOOGLE_API_KEY`: Your API key for Google AI Studio (Gemini).

The `BACKEND_URL` is pre-configured for the Docker network and should not need to be changed.

### 3. Running the System

To build and run all services in detached mode, use the following command:

```bash
docker-compose up --build -d
```

When you run the system for the first time, the `whatsapp` service will output a QR code in its logs. You need to scan this QR code with your phone to connect the bot to your WhatsApp account.

To view the logs for a specific service (e.g., to see the QR code from the `whatsapp` service):

```bash
docker-compose logs -f whatsapp
```

Or to see the logs for the backend:

```bash
docker-compose logs -f backend
```

---

## 🧪 Testing

The backend service includes a suite of tests using `pytest`. To run the tests, you can execute the following command from the root directory:

```bash
docker-compose exec backend pytest
```

This will run all tests inside the running `backend` container.

---

## ⚖️ License

This project is distributed under the MIT License. See the `LICENSE` file for more information.
