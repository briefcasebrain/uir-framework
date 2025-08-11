# UIR Framework Deployment Guide

## Overview

This guide covers deploying the Universal Information Retrieval (UIR) Framework in various environments, from local development to production Kubernetes clusters.

## Prerequisites

### System Requirements

#### Minimum Requirements (Development)
- **CPU**: 2 vCPUs
- **Memory**: 4 GB RAM
- **Storage**: 20 GB SSD
- **Network**: 10 Mbps
- **OS**: Linux, macOS, Windows (with WSL2)

#### Recommended Requirements (Production)
- **CPU**: 8+ vCPUs
- **Memory**: 16+ GB RAM
- **Storage**: 100+ GB SSD
- **Network**: 1 Gbps
- **Load Balancer**: Support for health checks and SSL termination

### Software Dependencies

#### Core Dependencies
- **Python**: 3.9 or higher
- **Redis**: 6.0 or higher (for caching)
- **PostgreSQL**: 13 or higher (for metadata storage)

#### Optional Dependencies
- **Docker**: 20.10 or higher
- **Kubernetes**: 1.24 or higher
- **Nginx**: 1.20 or higher (for reverse proxy)

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Core Settings
DEBUG=false
LOG_LEVEL=INFO
UIR_API_HOST=0.0.0.0
UIR_API_PORT=8000
WORKERS=4

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/uir_db
REDIS_URL=redis://localhost:6379/0

# Authentication
JWT_SECRET=your-super-secret-jwt-key-here
API_KEY_PREFIX=uir_
DEFAULT_RATE_LIMIT=1000

# Provider API Keys
GOOGLE_API_KEY=your-google-api-key
GOOGLE_CSE_ID=your-custom-search-engine-id
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
ELASTICSEARCH_URL=http://localhost:9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=your-password
OPENAI_API_KEY=your-openai-api-key

# Performance
DEFAULT_TIMEOUT_MS=5000
MAX_CONCURRENT_REQUESTS=100
CACHE_DEFAULT_TTL=3600

# Features
ENABLE_QUERY_EXPANSION=true
ENABLE_RESULT_CACHING=true
ENABLE_SPELL_CORRECTION=true
MOCK_MODE=false

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
JAEGER_ENDPOINT=http://jaeger:14268/api/traces
SENTRY_DSN=your-sentry-dsn
```

### Provider Configuration

Create `config/providers.yaml`:

```yaml
# Provider configurations
providers:
  google:
    enabled: true
    type: search_engine
    auth_method: api_key
    credentials:
      api_key: ${GOOGLE_API_KEY}
      cx: ${GOOGLE_CSE_ID}
    endpoints:
      search: https://www.googleapis.com/customsearch/v1
    rate_limits:
      default: 100
      burst: 10
    retry_policy:
      max_attempts: 3
      backoff_multiplier: 2
      max_backoff_ms: 10000
    timeout_ms: 5000
    circuit_breaker:
      failure_threshold: 5
      recovery_timeout_seconds: 60
      min_requests: 10

  pinecone:
    enabled: true
    type: vector_db
    auth_method: api_key
    credentials:
      api_key: ${PINECONE_API_KEY}
      environment: ${PINECONE_ENVIRONMENT}
      index_name: default
    rate_limits:
      default: 100
    timeout_ms: 3000
    circuit_breaker:
      failure_threshold: 3
      recovery_timeout_seconds: 30

  elasticsearch:
    enabled: true
    type: document_store
    auth_method: basic
    credentials:
      url: ${ELASTICSEARCH_URL}
      username: ${ELASTICSEARCH_USERNAME}
      password: ${ELASTICSEARCH_PASSWORD}
    timeout_ms: 5000
    
# Cache configuration
cache:
  redis:
    url: ${REDIS_URL}
    max_connections: 50
    max_connections_per_pool: 10
  local:
    max_size_mb: 100
    ttl_seconds: 3600

# Monitoring configuration  
monitoring:
  prometheus:
    enabled: true
    port: 9090
  logging:
    level: ${LOG_LEVEL}
    format: json
  tracing:
    enabled: true
    jaeger_endpoint: ${JAEGER_ENDPOINT}
```

## Deployment Options

### 1. Local Development

#### Using Python Virtual Environment

```bash
# Clone repository
git clone https://github.com/your-org/uir-framework.git
cd uir-framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export $(cat .env | xargs)

# Run database migrations
python -m src.uir.db.migrations upgrade

# Start development server
uvicorn src.uir.api.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Using Docker Compose (Recommended for Development)

```bash
# Clone repository
git clone https://github.com/your-org/uir-framework.git
cd uir-framework

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f uir-api

# Stop services
docker-compose down
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  uir-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://uir:password@postgres:5432/uir_db
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    volumes:
      - ./config:/app/config
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: uir_db
      POSTGRES_USER: uir
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

### 2. Production Docker Deployment

#### Multi-Stage Dockerfile

```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

# Create non-root user
RUN groupadd -g 1001 uir && \
    useradd -r -u 1001 -g uir uir

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /root/.local /home/uir/.local

# Set up application
WORKDIR /app
COPY --chown=uir:uir src/ ./src/
COPY --chown=uir:uir config/ ./config/
COPY --chown=uir:uir requirements.txt .

# Set environment variables
ENV PATH=/home/uir/.local/bin:$PATH
ENV PYTHONPATH=/app

# Switch to non-root user
USER uir

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "src.uir.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

#### Production Docker Compose

```yaml
version: '3.8'

services:
  uir-api:
    image: uir-framework:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://uir:${DB_PASSWORD}@postgres:5432/uir_db
      - REDIS_URL=redis://redis:6379/0
      - WORKERS=4
      - DEBUG=false
    secrets:
      - db_password
      - jwt_secret
      - google_api_key
      - pinecone_api_key
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: uir_db
      POSTGRES_USER: uir
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    secrets:
      - db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          memory: 512M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - uir-api
    deploy:
      replicas: 2

secrets:
  db_password:
    external: true
  jwt_secret:
    external: true
  google_api_key:
    external: true
  pinecone_api_key:
    external: true

volumes:
  postgres_data:
  redis_data:
```

### 3. Kubernetes Deployment

#### Namespace and ConfigMap

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: uir-framework
  labels:
    name: uir-framework

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: uir-config
  namespace: uir-framework
data:
  LOG_LEVEL: "INFO"
  DEBUG: "false"
  WORKERS: "4"
  DEFAULT_TIMEOUT_MS: "5000"
  ENABLE_QUERY_EXPANSION: "true"
  ENABLE_RESULT_CACHING: "true"
```

#### Secrets

```yaml
# secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: uir-secrets
  namespace: uir-framework
type: Opaque
stringData:
  DATABASE_URL: "postgresql://uir:password@postgres:5432/uir_db"
  REDIS_URL: "redis://redis:6379/0"
  JWT_SECRET: "your-jwt-secret"
  GOOGLE_API_KEY: "your-google-api-key"
  PINECONE_API_KEY: "your-pinecone-api-key"
  OPENAI_API_KEY: "your-openai-api-key"
```

#### Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: uir-api
  namespace: uir-framework
  labels:
    app: uir-api
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  selector:
    matchLabels:
      app: uir-api
  template:
    metadata:
      labels:
        app: uir-api
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      containers:
      - name: uir-api
        image: uir-framework:1.0.0
        ports:
        - containerPort: 8000
          name: http
        - containerPort: 9090
          name: metrics
        envFrom:
        - configMapRef:
            name: uir-config
        - secretRef:
            name: uir-secrets
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
          timeoutSeconds: 10
          failureThreshold: 3
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        securityContext:
          runAsNonRoot: true
          runAsUser: 1001
          runAsGroup: 1001
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
        volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: config
          mountPath: /app/config
          readOnly: true
      volumes:
      - name: tmp
        emptyDir: {}
      - name: config
        configMap:
          name: uir-providers-config
      securityContext:
        fsGroup: 1001
```

#### Service and Ingress

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: uir-api-service
  namespace: uir-framework
  labels:
    app: uir-api
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
    name: http
  - port: 9090
    targetPort: 9090
    name: metrics
  selector:
    app: uir-api

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: uir-api-ingress
  namespace: uir-framework
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
spec:
  tls:
  - hosts:
    - api.uir-framework.com
    secretName: uir-api-tls
  rules:
  - host: api.uir-framework.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: uir-api-service
            port:
              number: 8000
```

#### Horizontal Pod Autoscaler

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: uir-api-hpa
  namespace: uir-framework
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: uir-api
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

#### Database (PostgreSQL)

```yaml
# postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: uir-framework
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: uir_db
        - name: POSTGRES_USER
          value: uir
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 1
            memory: 2Gi
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - exec pg_isready -U uir -d uir_db -h 127.0.0.1 -p 5432
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 6
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - exec pg_isready -U uir -d uir_db -h 127.0.0.1 -p 5432
          initialDelaySeconds: 5
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: fast-ssd
      resources:
        requests:
          storage: 100Gi

---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: uir-framework
spec:
  type: ClusterIP
  ports:
  - port: 5432
    targetPort: 5432
  selector:
    app: postgres
```

#### Redis

```yaml
# redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: uir-framework
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command: ["redis-server", "--appendonly", "yes"]
        ports:
        - containerPort: 6379
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 1Gi
        volumeMounts:
        - name: redis-storage
          mountPath: /data
        livenessProbe:
          tcpSocket:
            port: 6379
          initialDelaySeconds: 30
          periodSeconds: 5
        readinessProbe:
          exec:
            command:
            - redis-cli
            - ping
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: redis-storage
        persistentVolumeClaim:
          claimName: redis-pvc

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: uir-framework
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 20Gi

---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: uir-framework
spec:
  type: ClusterIP
  ports:
  - port: 6379
    targetPort: 6379
  selector:
    app: redis
```

## Deployment Commands

### Docker Commands

```bash
# Build image
docker build -t uir-framework:latest .

# Run with environment file
docker run --env-file .env -p 8000:8000 uir-framework:latest

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f uir-api

# Scale services
docker-compose up -d --scale uir-api=3

# Update service
docker-compose pull uir-api
docker-compose up -d uir-api
```

### Kubernetes Commands

```bash
# Apply all configurations
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -n uir-framework
kubectl get services -n uir-framework
kubectl get ingress -n uir-framework

# View logs
kubectl logs -f deployment/uir-api -n uir-framework

# Scale deployment
kubectl scale deployment uir-api --replicas=5 -n uir-framework

# Update image
kubectl set image deployment/uir-api uir-api=uir-framework:1.1.0 -n uir-framework

# Check rollout status
kubectl rollout status deployment/uir-api -n uir-framework

# Rollback if needed
kubectl rollout undo deployment/uir-api -n uir-framework
```

## Monitoring and Observability

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
- job_name: 'uir-api'
  static_configs:
  - targets: ['uir-api:9090']
  metrics_path: '/metrics'
  scrape_interval: 30s

- job_name: 'postgres'
  static_configs:
  - targets: ['postgres-exporter:9187']

- job_name: 'redis'
  static_configs:
  - targets: ['redis-exporter:9121']

rule_files:
- "uir-alerts.yml"

alerting:
  alertmanagers:
  - static_configs:
    - targets:
      - alertmanager:9093
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "UIR Framework Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(uir_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Response Time", 
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(uir_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      },
      {
        "title": "Provider Health",
        "type": "stat",
        "targets": [
          {
            "expr": "uir_provider_health",
            "legendFormat": "{{provider}}"
          }
        ]
      }
    ]
  }
}
```

### Alerting Rules

```yaml
# uir-alerts.yml
groups:
- name: uir-framework
  rules:
  - alert: HighErrorRate
    expr: rate(uir_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High error rate detected
      description: Error rate is {{ $value }} errors per second

  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(uir_request_duration_seconds_bucket[5m])) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: High response time detected
      description: 95th percentile response time is {{ $value }} seconds

  - alert: ProviderDown
    expr: uir_provider_health == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: Provider {{ $labels.provider }} is down
      description: Provider {{ $labels.provider }} has been unhealthy for more than 2 minutes
```

## Security Configuration

### TLS/SSL Configuration

```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name api.uir-framework.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    location / {
        proxy_pass http://uir-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }
}

# Rate limiting
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
}
```

### Network Security

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: uir-api-network-policy
  namespace: uir-framework
spec:
  podSelector:
    matchLabels:
      app: uir-api
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:
    - podSelector:
        matchLabels:
          app: redis
    ports:
    - protocol: TCP
      port: 6379
  - to: []  # Allow external API calls
    ports:
    - protocol: TCP
      port: 443
```

## Backup and Disaster Recovery

### Database Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/uir"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="uir_db"
DB_USER="uir"
DB_HOST="postgres"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME --clean --create --if-exists \
    | gzip > $BACKUP_DIR/uir_db_$DATE.sql.gz

# Remove backups older than 7 days
find $BACKUP_DIR -name "uir_db_*.sql.gz" -mtime +7 -delete

echo "Backup completed: uir_db_$DATE.sql.gz"
```

### Kubernetes Backup using Velero

```bash
# Install Velero
kubectl apply -f https://github.com/vmware-tanzu/velero/releases/download/v1.11.0/00-prereqs.yaml

# Create backup
velero backup create uir-backup --include-namespaces uir-framework

# Schedule daily backups
velero schedule create uir-daily --schedule="0 1 * * *" --include-namespaces uir-framework

# Restore from backup
velero restore create --from-backup uir-backup
```

## Performance Tuning

### Application Tuning

```python
# production_config.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "src.uir.api.main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # CPU cores
        worker_class="uvicorn.workers.UvicornWorker",
        max_requests=1000,  # Restart worker after N requests
        max_requests_jitter=50,
        preload_app=True,  # Pre-load app in master process
        keep_alive=2,
        access_log=False,  # Disable for performance
        use_colors=False
    )
```

### Database Tuning

```sql
-- postgresql.conf optimizations
shared_buffers = 1GB
effective_cache_size = 3GB
work_mem = 16MB
maintenance_work_mem = 512MB
max_connections = 100
random_page_cost = 1.1
effective_io_concurrency = 200

-- Create indexes
CREATE INDEX idx_search_results_provider ON search_results(provider);
CREATE INDEX idx_search_results_query_hash ON search_results USING hash(query_hash);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_usage_stats_date ON usage_stats(date);
```

### Redis Tuning

```conf
# redis.conf
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
tcp-keepalive 300
timeout 0
```

## Troubleshooting

### Common Issues

#### High Memory Usage
```bash
# Check memory usage
kubectl top pods -n uir-framework

# Check for memory leaks
kubectl exec -it deployment/uir-api -n uir-framework -- python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'CPU: {psutil.cpu_percent()}%')
"
```

#### Database Connection Issues
```bash
# Check database connectivity
kubectl exec -it deployment/uir-api -n uir-framework -- python -c "
import psycopg2
conn = psycopg2.connect(host='postgres', database='uir_db', user='uir', password='password')
print('Database connection successful')
"
```

#### Provider API Errors
```bash
# Check provider health
curl -H "Authorization: Bearer <api_key>" https://api.uir-framework.com/providers

# Enable debug logging
kubectl set env deployment/uir-api LOG_LEVEL=DEBUG -n uir-framework
```

### Log Analysis

```bash
# View application logs
kubectl logs -f deployment/uir-api -n uir-framework | jq '.'

# Search for errors
kubectl logs deployment/uir-api -n uir-framework --since=1h | grep ERROR

# Monitor performance
kubectl logs deployment/uir-api -n uir-framework | grep "query_time_ms" | tail -100
```

This comprehensive deployment guide provides everything needed to successfully deploy and operate the UIR Framework in production environments.