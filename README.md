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

---

## 🚀 Production Deployment

This project is configured for fully automated deployments to a production environment using GitHub Actions.

### CI/CD Pipeline

The deployment pipeline is defined in `.github/workflows/deploy.yml` and consists of three stages:

1.  **Test and Lint:** Automatically runs all tests and code quality checks for the backend and frontend. This job must pass before the deployment can proceed.
2.  **Build and Push:** Builds new Docker images for the `backend`, `frontend`, and `whatsapp` services. These images are tagged with `latest` and pushed to Docker Hub.
3.  **Deploy:** Connects to the production server via SSH, pulls the latest Docker images from Docker Hub, and restarts the services using `docker-compose.prod.yml`.

This process ensures that every push to the `main` branch that passes the tests is automatically deployed to production.

### Environment Configuration

For production, you must create a `.env.prod` file in the root of the project on your server. **This file should not be committed to version control.**

```bash
# .env.prod - Production Environment Variables

# General
NODE_ENV=production
PYTHON_ENV=production
DEBUG=False

# Supabase Configuration (for backend)
SUPABASE_URL="your-prod-supabase-url"
SUPABASE_KEY="your-prod-supabase-service-role-key"

# Google AI Configuration (for backend)
GOOGLE_API_KEY="your-prod-google-api-key"

# WhatsApp Adapter Configuration
BACKEND_URL="http://nginx/api/chat"

# Domain and Email for SSL
DOMAIN_NAME="your-domain.com"
CERTBOT_EMAIL="your-email@domain.com"
```

### GitHub Secrets

The CI/CD workflow requires several secrets to be configured in your GitHub repository settings under **Settings > Secrets and variables > Actions**.

#### Required Secrets:

-   `DOCKERHUB_USERNAME`: Your username for Docker Hub.
-   `DOCKERHUB_TOKEN`: An access token for Docker Hub with read/write permissions.
-   `VPS_HOST`: The IP address or domain name of your production server.
-   `VPS_USERNAME`: The username for SSH access to your production server.
-   `VPS_SSH_KEY`: The private SSH key for accessing your production server.
-   `VPS_PORT`: The SSH port for your production server (usually 22).

### Manual Setup on the Server

Before the first deployment, you need to:

1.  Clone this repository to your production server.
2.  Create the `.env.prod` file with your production values.
3.  Run an initial `docker-compose -f docker-compose.prod.yml up -d` to create the necessary volumes.
4.  Manually run the Certbot command inside the `docker-compose.prod.yml` to generate the initial SSL certificates. After the first run, the certificates will be renewed automatically.
