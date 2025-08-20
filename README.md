# EVA: AI Sales Agent Platform

EVA is a multi-tenant SaaS platform for deploying AI-powered sales agents. This repository contains the complete, containerized infrastructure for the platform, designed for automated deployment and scalability.

The system follows a microservice architecture and is orchestrated entirely by Docker Compose. All services, including the frontend, are designed to run on a single production server.

## Architecture Overview

-   **`frontend` (Next.js):** The user-facing dashboard for managing agents, viewing conversations, and configuring accounts. It is served as a Docker container.
-   **`main-api` (Python/FastAPI):** The core of the application. It handles all business logic, manages AI model routing, and serves the primary REST API. It communicates with other services asynchronously.
-   **`whatsapp-gateway` (Node.js):** The entry point for all user messages from WhatsApp. It acts as a bridge, receiving messages, uploading media, and publishing events to a Redis stream.
-   **`transcription-worker` (Python):** A dedicated worker that listens for audio messages on the Redis stream, transcribes them using Google Speech-to-Text, and publishes the text back for the `main-api` to process.
-   **`nginx` (Nginx):** A reverse proxy that routes incoming traffic to the appropriate service (`frontend` or `main-api`) and handles SSL termination with auto-renewing certificates from Let's Encrypt.
-   **`redis` (Redis):** Used as a high-performance message broker (via Redis Streams) to facilitate asynchronous communication between the microservices.
-   **`loki` & `promtail`:** A comprehensive logging stack to aggregate and view logs from all running containers.

---

## 🚀 Getting Started

### 1. Prerequisites

-   Docker & Docker Compose
-   A registered domain name pointing to your server's IP address.
-   A Docker Hub account for image storage.

### 2. Environment Variables

The entire system is configured using environment variables. For local development or production, copy the example file:

```bash
cp .env.example .env.prod
```

Then, fill in the values in `.env.prod`. Refer to the comments in the file for guidance on each variable.

### 3. Running the System Locally

To build and run all services in detached mode, use the production docker-compose file, which is the single source of truth for the project's architecture:

```bash
docker-compose -f docker-compose.prod.yml up --build -d
```

To view the logs for a specific service (e.g., `whatsapp-gateway` to scan the QR code):

```bash
docker-compose -f docker-compose.prod.yml logs -f whatsapp-gateway
```

---

## 🧪 Testing

The project includes an automated testing suite for both backend and frontend, which is executed automatically in the CI/CD pipeline.

To run the tests manually, first ensure the services are running:

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Wait a few seconds for services to initialize, then run tests
```

-   **Backend Tests (`main-api`):**
    ```bash
    docker-compose -f docker-compose.prod.yml exec main-api pytest
    ```

-   **Frontend Tests:**
    ```bash
    docker-compose -f docker-compose.prod.yml exec frontend npm test
    ```

---

## 🚀 Production Deployment (CI/CD)

This project is configured for **fully automated deployments** to a production environment using GitHub Actions.

### How It Works

The deployment pipeline is defined in `.github/workflows/deploy.yml` and triggers on every push to the `main` branch. It consists of three stages:

1.  **Test and Lint:** Automatically runs all tests and code quality checks for all services. This job must pass before deployment can proceed.
2.  **Build and Push:** Builds new Docker images for all services, tags them with `latest`, and pushes them to your Docker Hub registry.
3.  **Deploy:** Connects to the production server via SSH, creates the `.env.prod` file from GitHub Secrets, pulls the latest Docker images from Docker Hub, and restarts the services using `docker-compose.prod.yml`.

### GitHub Secrets Configuration

For the automation to work, you must configure the following secrets in your GitHub repository settings under **Settings > Secrets and variables > Actions**:

-   `DOCKERHUB_USERNAME`: Your username for Docker Hub.
-   `DOCKERHUB_TOKEN`: A Docker Hub access token with read/write permissions.
-   `SSH_HOST`: The IP address or domain of your production server.
-   `SSH_USERNAME`: The username for SSH access.
-   `SSH_PRIVATE_KEY`: The private SSH key for accessing the server.
-   `DOMAIN_NAME`: The domain name for your service (e.g., `eva.yourcompany.com`).
-   `CERTBOT_EMAIL`: The email address for Let's Encrypt notifications.
-   All other secrets required by the application (e.g., `SUPABASE_URL`, `GOOGLE_API_KEY`, etc.).

With this setup, your infrastructure is fully automated. Simply push to `main`, and your changes will be tested and deployed.
