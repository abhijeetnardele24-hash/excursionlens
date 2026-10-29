# Stage 1: Build Frontend Assets
FROM node:20-alpine AS frontend-builder
WORKDIR /web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web ./
RUN npm run build

# Stage 2: Production Python Runtime
FROM python:3.11-slim AS runner
WORKDIR /app

ARG GIT_COMMIT=unknown
ENV APP_COMMIT_SHA=${GIT_COMMIT}

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code, fixtures, and benchmark datasets
COPY apps/api ./apps/api
COPY packages/fixtures ./packages/fixtures
COPY benchmark ./benchmark

# Copy prebuilt frontend static assets from builder stage
COPY --from=frontend-builder /web/dist ./apps/web/dist

# Create dedicated non-root application user and set ownership
RUN groupadd -r appuser && useradd -r -g appuser -u 10001 -d /app -s /sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser

# Expose standard port
EXPOSE 8000

ENV PYTHONPATH=.
ENV HOST=0.0.0.0
ENV PORT=8000
ENV APPLICATION_ENVIRONMENT=docker

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Start FastAPI production server
CMD ["python", "-m", "uvicorn", "apps.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
