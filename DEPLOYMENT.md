# Collections Backend API - Docker & Deployment Guide

This guide covers Docker containerization, deployment strategies, and production setup for the Collections Backend API service.

## Docker Setup

### Basic Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"]
```

### Docker Compose for Development

Create `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  collections-api:
    build: 
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - LOG_LEVEL=DEBUG
      - DEBUG=true
    env_file:
      - .env
    volumes:
      # Mount source for hot reloading in development
      - .:/app
      - /app/__pycache__
    depends_on:
      - supabase
    networks:
      - collections-network
    restart: unless-stopped

  # Optional: Local Supabase for development
  supabase:
    image: supabase/postgres:15.1.0.117
    environment:
      POSTGRES_DB: collections
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - supabase_data:/var/lib/postgresql/data
      - ./docker/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    networks:
      - collections-network

volumes:
  supabase_data:

networks:
  collections-network:
    driver: bridge
```

### Docker Compose for Production

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  collections-api:
    build: 
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
      - LOG_LEVEL=WARNING
      - DEBUG=false
    env_file:
      - .env.production
    restart: always
    networks:
      - collections-network
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf
      - ./docker/ssl:/etc/ssl/certs
    depends_on:
      - collections-api
    networks:
      - collections-network
    restart: always

  # Redis for caching (optional)
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - collections-network
    restart: always

volumes:
  redis_data:

networks:
  collections-network:
    driver: bridge
```

### Nginx Configuration

Create `docker/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream collections_api {
        server collections-api:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;

    server {
        listen 80;
        server_name your-domain.com;

        # Security headers
        add_header X-Content-Type-Options nosniff;
        add_header X-Frame-Options DENY;
        add_header X-XSS-Protection "1; mode=block";

        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://collections_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS handling
            if ($request_method = 'OPTIONS') {
                add_header 'Access-Control-Allow-Origin' '$http_origin';
                add_header 'Access-Control-Allow-Methods' 'GET, POST, PATCH, OPTIONS';
                add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization';
                add_header 'Access-Control-Max-Age' 1728000;
                add_header 'Content-Type' 'text/plain; charset=utf-8';
                add_header 'Content-Length' 0;
                return 204;
            }
        }

        # Health check endpoint
        location /health {
            proxy_pass http://collections_api/health;
            access_log off;
        }

        # Documentation
        location ~ ^/(docs|redoc) {
            proxy_pass http://collections_api;
            proxy_set_header Host $host;
        }
    }
}
```

## Deployment Strategies

### 1. Cloud Platform Deployment

#### **AWS Deployment (ECS/Fargate)**

Create `docker/aws/task-definition.json`:

```json
{
  "family": "collections-backend-api",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "collections-api",
      "image": "your-ecr-repo/collections-backend-api:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "HOST", "value": "0.0.0.0"},
        {"name": "PORT", "value": "8000"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {
          "name": "SUPABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:collections/supabase-url"
        },
        {
          "name": "SUPABASE_ANON_KEY", 
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:collections/supabase-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/collections-backend-api",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

#### **Google Cloud Run Deployment**

Create `docker/gcp/cloudbuild.yaml`:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/collections-backend-api:$COMMIT_SHA', '.']

  # Push the container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/collections-backend-api:$COMMIT_SHA']

  # Deploy container image to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
    - 'run'
    - 'deploy'
    - 'collections-backend-api'
    - '--image'
    - 'gcr.io/$PROJECT_ID/collections-backend-api:$COMMIT_SHA'
    - '--region'
    - 'us-central1'
    - '--platform'
    - 'managed'
    - '--port'
    - '8000'
    - '--set-env-vars'
    - 'HOST=0.0.0.0,PORT=8000'
    - '--allow-unauthenticated'

images:
- gcr.io/$PROJECT_ID/collections-backend-api:$COMMIT_SHA
```

#### **Azure Container Instances**

Create `docker/azure/deploy.sh`:

```bash
#!/bin/bash

# Set variables
RESOURCE_GROUP="collections-rg"
CONTAINER_NAME="collections-backend-api"
REGISTRY_NAME="collectionsregistry"

# Create resource group
az group create --name $RESOURCE_GROUP --location eastus

# Create Azure Container Registry
az acr create --resource-group $RESOURCE_GROUP \
  --name $REGISTRY_NAME --sku Basic

# Build and push image
az acr build --registry $REGISTRY_NAME \
  --image collections-backend-api:latest .

# Deploy container
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $CONTAINER_NAME \
  --image $REGISTRY_NAME.azurecr.io/collections-backend-api:latest \
  --cpu 1 --memory 1 \
  --registry-login-server $REGISTRY_NAME.azurecr.io \
  --registry-username $REGISTRY_NAME \
  --registry-password $(az acr credential show --name $REGISTRY_NAME --query "passwords[0].value" -o tsv) \
  --dns-name-label collections-api \
  --ports 8000 \
  --environment-variables \
    HOST=0.0.0.0 \
    PORT=8000 \
    LOG_LEVEL=INFO \
  --secure-environment-variables \
    SUPABASE_URL=$SUPABASE_URL \
    SUPABASE_ANON_KEY=$SUPABASE_ANON_KEY
```

### 2. Kubernetes Deployment

#### **Kubernetes Manifests**

Create `k8s/namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: collections
```

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: collections-backend-api
  namespace: collections
  labels:
    app: collections-backend-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: collections-backend-api
  template:
    metadata:
      labels:
        app: collections-backend-api
    spec:
      containers:
      - name: api
        image: your-registry/collections-backend-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: HOST
          value: "0.0.0.0"
        - name: PORT
          value: "8000"
        - name: LOG_LEVEL
          value: "INFO"
        envFrom:
        - secretRef:
            name: collections-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

Create `k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: collections-backend-api-service
  namespace: collections
spec:
  selector:
    app: collections-backend-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: ClusterIP
```

Create `k8s/ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: collections-backend-api-ingress
  namespace: collections
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  rules:
  - host: api.collections.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: collections-backend-api-service
            port:
              number: 80
```

Create `k8s/secrets.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: collections-secrets
  namespace: collections
type: Opaque
data:
  SUPABASE_URL: <base64-encoded-url>
  SUPABASE_ANON_KEY: <base64-encoded-key>
  MONITOR_API_URL: <base64-encoded-monitor-url>
```

## Production Environment Setup

### 1. Environment Variable Management

#### **Production .env.production**
```bash
# Production Supabase
SUPABASE_URL=https://prod-project.supabase.co
SUPABASE_ANON_KEY=prod_anon_key_here

# Production Collections Monitor
MONITOR_API_URL=https://collections-monitor.company.com

# Production Frontend
FRONTEND_URL=https://dashboard.company.com

# Production Settings
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=WARNING
DEBUG=false

# Monitoring
SENTRY_DSN=https://sentry-dsn-here
NEW_RELIC_LICENSE_KEY=newrelic-key-here
```

#### **Secret Management Best Practices**
```bash
# Use secret management systems
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name collections/supabase-credentials \
  --description "Supabase credentials for Collections API" \
  --secret-string '{"url":"https://...","key":"eyJ..."}'

# Google Secret Manager
gcloud secrets create supabase-url --data-file=url.txt
gcloud secrets create supabase-key --data-file=key.txt

# Azure Key Vault
az keyvault secret set \
  --vault-name collections-vault \
  --name supabase-url \
  --value "https://..."
```

### 2. Monitoring & Observability

#### **Health Check Configuration**
```python
# Enhanced health check in main.py
@app.get("/health")
async def enhanced_health_check():
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {}
    }
    
    # Check Supabase connection
    try:
        if SUPABASE_AVAILABLE:
            result = supabase.table('collections_queue').select('count').limit(1).execute()
            health_status["checks"]["supabase"] = "healthy"
        else:
            health_status["checks"]["supabase"] = "unavailable"
    except Exception as e:
        health_status["checks"]["supabase"] = f"error: {str(e)}"
    
    # Check Collections Monitor
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MONITOR_API_URL}/health", timeout=5.0)
            health_status["checks"]["collections_monitor"] = "healthy" if response.status_code == 200 else "unhealthy"
    except Exception:
        health_status["checks"]["collections_monitor"] = "unavailable"
    
    return health_status
```

#### **Logging Configuration**
```python
# Production logging setup
import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_production_logging():
    """Configure production-ready logging"""
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler with rotation
    file_handler = RotatingFileHandler(
        'collections-api.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.WARNING,
        handlers=[console_handler, file_handler]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
```

### 3. Performance Optimization

#### **Production Dockerfile with Optimizations**
```dockerfile
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Production stage
FROM python:3.11-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy wheels and install
COPY --from=builder /app/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy application
COPY . .

# Security: non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Performance: precompile Python files
RUN python -m compileall .

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "-O", "main.py"]
```

## Deployment Automation

### 1. CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Collections Backend API

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/ --cov=main --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Checkout
      uses: actions/checkout@v3
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest,${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
    
    - name: Deploy to production
      run: |
        # Add your deployment script here
        echo "Deploy to production infrastructure"
```

### 2. Deployment Scripts

Create `scripts/deploy.sh`:

```bash
#!/bin/bash
set -e

# Deployment script for Collections Backend API

# Configuration
DOCKER_IMAGE="collections-backend-api"
CONTAINER_NAME="collections-api"
ENV_FILE=".env.production"

echo "🚀 Starting deployment..."

# Pull latest code
git pull origin main

# Stop existing container
echo "📦 Stopping existing container..."
docker stop $CONTAINER_NAME || true
docker rm $CONTAINER_NAME || true

# Build new image
echo "🔨 Building Docker image..."
docker build -t $DOCKER_IMAGE .

# Run new container
echo "▶️ Starting new container..."
docker run -d \
  --name $CONTAINER_NAME \
  --env-file $ENV_FILE \
  -p 8000:8000 \
  --restart unless-stopped \
  $DOCKER_IMAGE

# Wait for health check
echo "🏥 Waiting for health check..."
sleep 10

# Verify deployment
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
  echo "✅ Deployment successful!"
else
  echo "❌ Deployment failed - health check failed"
  docker logs $CONTAINER_NAME
  exit 1
fi

# Cleanup old images
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "🎉 Deployment completed successfully!"
```

## Security Considerations

### 1. Container Security
```dockerfile
# Security-hardened Dockerfile
FROM python:3.11-slim

# Security updates
RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Non-root user
RUN groupadd -r app && useradd -r -g app app

# Set secure permissions
WORKDIR /app
COPY --chown=app:app . .
USER app

# Remove unnecessary packages
RUN pip uninstall -y pip setuptools wheel
```

### 2. Network Security
```yaml
# docker-compose with network security
version: '3.8'
services:
  collections-api:
    build: .
    networks:
      - internal
      - external
    ports:
      - "127.0.0.1:8000:8000"  # Bind only to localhost

networks:
  internal:
    internal: true
  external:
```

---

This deployment guide provides comprehensive options for deploying the Collections Backend API in various environments, from simple Docker containers to sophisticated Kubernetes clusters. Choose the deployment strategy that best fits your infrastructure and requirements.