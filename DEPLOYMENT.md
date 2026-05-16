# Veyra Deployment Guide

This guide covers deploying the full Veyra stack (FastAPI, LangGraph, PostgreSQL, Redis, Next.js, Nginx) to various production environments.

## 1. Local Production (Docker Compose)
The easiest way to run the entire stack locally or on a single VPS.

```bash
# 1. Create a .env file based on .env.example
cp .env.example .env

# 2. Add your OPENAI_API_KEY and secure passwords to .env
# REDIS_PASSWORD=secure_redis_pass
# POSTGRES_PASSWORD=secure_db_pass
# DOMAIN=yourdomain.com

# 3. Build and run detached
docker-compose -f docker-compose.prod.yml up -d --build
```
> **Note on Nginx SSL:** For HTTPS, you will need to map your SSL certificates to `/etc/nginx/certs` and update `docker/nginx/nginx.conf` to listen on 443 with `ssl_certificate` directives. Let's Encrypt / Certbot is recommended.

## 2. Managed PaaS (Render / Railway)
Managed platforms are ideal for zero-downtime scaling without managing servers.

### Render
1. **Database:** Create a new PostgreSQL instance on Render. Note the Internal DB URL.
2. **Redis:** Create a new Redis instance. Note the Internal Redis URL.
3. **Backend API (Web Service):**
   - Environment: `Docker`
   - Dockerfile: `docker/backend.Dockerfile`
   - Env Vars: `DATABASE_URL`, `REDIS_URL`, `OPENAI_API_KEY`
4. **Celery Worker (Background Worker):**
   - Environment: `Docker`
   - Dockerfile: `docker/backend.Dockerfile`
   - Start Command: `celery -A backend.app.worker.celery_app worker --loglevel=info`
   - Env Vars: Same as Backend API.
5. **Frontend (Web Service):**
   - Environment: `Docker`
   - Dockerfile: `docker/frontend.Dockerfile`
   - Context: `./frontend`
   - Env Vars: `NEXT_PUBLIC_API_URL=https://<your-backend-render-url>/api/v1` and `NEXT_PUBLIC_WS_URL=wss://<your-backend-render-url>/api/v1`

### Railway
Use the `Railway CLI` or UI to link the GitHub repo. Railway natively understands `docker-compose.yml`, but it's recommended to deploy components individually:
1. Add PostgreSQL & Redis plugins.
2. Deploy backend pointing to `docker/backend.Dockerfile`.
3. Deploy frontend pointing to `docker/frontend.Dockerfile`.
4. Link environment variables via Railway Variables UI.

## 3. AWS ECS (Elastic Container Service)
For enterprise scalability:
1. **ECR:** Push images via the included GitHub Actions workflow.
2. **RDS / ElastiCache:** Provision managed Postgres and Redis instances. Ensure security groups allow access from ECS.
3. **Task Definitions:**
   - **Backend Task:** Map port 8000.
   - **Worker Task:** Same image, override command to run Celery.
   - **Frontend Task:** Map port 3000.
4. **ALB (Application Load Balancer):** Route `/api/*` to the Backend target group, and `/*` to the Frontend target group. Ensure WebSocket support is enabled on the ALB attributes.

## 4. DigitalOcean / Single VPS
For a cost-effective custom setup:
1. Provision a Droplet (Ubuntu 22.04, 4GB+ RAM recommended for Chroma/DB/Redis).
2. Install Docker & Docker Compose.
3. Clone repository.
4. Configure `.env`.
5. Run `docker-compose -f docker-compose.prod.yml up -d`.
6. Set up Cloudflare DNS pointing to your Droplet IP.
7. Use `Certbot` with a reverse proxy manager (like Nginx Proxy Manager or Traefik) instead of the raw Nginx container if you want automatic SSL renewals.

## Production Checklist & Security Hardening
- [ ] **Change default passwords:** Never use `postgres`/`redispass` in prod.
- [ ] **Lock down CORS:** Update `BACKEND_CORS_ORIGINS` in FastAPI settings to strictly your frontend domain.
- [ ] **Authentication:** Replace the mock user ID in `deps.py` with a valid JWT OAuth2 provider (Auth0, Clerk, Cognito).
- [ ] **Rate Limiting:** Add `slowapi` or Redis-based rate limiting to the FastAPI endpoints.
- [ ] **ChromaDB Storage:** Ensure `/app/var` is mounted as a persistent volume. If running horizontally distributed (e.g., multiple ECS nodes), consider migrating Chroma to a standalone Client/Server deployment rather than embedding it inside the FastAPI pods.
