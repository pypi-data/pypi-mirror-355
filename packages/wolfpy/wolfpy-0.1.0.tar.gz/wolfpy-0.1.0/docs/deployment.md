# 🚀 WolfPy Deployment Guide

This guide covers deploying WolfPy applications to production environments.

## 📋 Pre-deployment Checklist

Before deploying your WolfPy application:

- [ ] Set `debug=False` in production
- [ ] Configure secure `SECRET_KEY`
- [ ] Set up production database
- [ ] Configure environment variables
- [ ] Run security checks
- [ ] Set up logging
- [ ] Configure static file serving
- [ ] Set up SSL/HTTPS
- [ ] Configure monitoring

## 🔧 Production Configuration

### Environment Variables

Create a `.env` file for production settings:

```bash
# .env
WOLFPY_ENV=production
DEBUG=False
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/dbname
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Application Configuration

```python
# config/production.py
import os
from pathlib import Path

class ProductionConfig:
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    DATABASE_URL = os.getenv('DATABASE_URL')
    REDIS_URL = os.getenv('REDIS_URL')
    
    # Security settings
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    
    # Static files
    STATIC_ROOT = Path(__file__).parent.parent / 'staticfiles'
    STATIC_URL = '/static/'
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = '/var/log/wolfpy/app.log'

# app.py
from config.production import ProductionConfig

app = WolfPy(
    debug=ProductionConfig.DEBUG,
    secret_key=ProductionConfig.SECRET_KEY,
    database_url=ProductionConfig.DATABASE_URL
)
```

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/wolfpy
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./staticfiles:/app/staticfiles
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: wolfpy
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./staticfiles:/var/www/static
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
```

### Build and Deploy

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f web

# Scale application
docker-compose up -d --scale web=3
```

## ☁️ Cloud Platform Deployment

### Heroku

```bash
# Install Heroku CLI and login
heroku login

# Create Heroku app
heroku create your-app-name

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Add Redis addon
heroku addons:create heroku-redis:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=your-secret-key
heroku config:set WOLFPY_ENV=production

# Deploy
git push heroku main

# Run migrations
heroku run python manage.py migrate

# Scale dynos
heroku ps:scale web=2
```

Create `Procfile`:
```
web: gunicorn --config gunicorn.conf.py app:app
worker: python worker.py
```

### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init

# Create environment
eb create production

# Deploy
eb deploy

# View logs
eb logs
```

### DigitalOcean App Platform

Create `app.yaml`:
```yaml
name: wolfpy-app
services:
- name: web
  source_dir: /
  github:
    repo: your-username/your-repo
    branch: main
  run_command: gunicorn --config gunicorn.conf.py app:app
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: SECRET_KEY
    value: your-secret-key
  - key: DATABASE_URL
    value: ${db.DATABASE_URL}
databases:
- name: db
  engine: PG
  version: "13"
```

## 🌐 Traditional Server Deployment

### Ubuntu/Debian Server

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv nginx postgresql redis-server

# Create application user
sudo useradd --system --shell /bin/bash --home /opt/wolfpy wolfpy

# Set up application directory
sudo mkdir -p /opt/wolfpy
sudo chown wolfpy:wolfpy /opt/wolfpy

# Switch to app user
sudo -u wolfpy -i

# Clone and set up application
cd /opt/wolfpy
git clone https://github.com/your-username/your-app.git app
cd app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with production values

# Test application
python app.py
```

### Systemd Service

Create `/etc/systemd/system/wolfpy.service`:

```ini
[Unit]
Description=WolfPy Application
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=wolfpy
Group=wolfpy
WorkingDirectory=/opt/wolfpy/app
Environment=PATH=/opt/wolfpy/app/venv/bin
ExecStart=/opt/wolfpy/app/venv/bin/gunicorn --config gunicorn.conf.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable wolfpy
sudo systemctl start wolfpy
sudo systemctl status wolfpy
```

### Nginx Configuration

Create `/etc/nginx/sites-available/wolfpy`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL configuration
    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # Static files
    location /static/ {
        alias /opt/wolfpy/app/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/wolfpy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 📊 Monitoring and Logging

### Application Monitoring

```python
# monitoring.py
import logging
import time
from functools import wraps

def monitor_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logging.info(f"{func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logging.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    return wrapper

# Usage
@app.route('/api/data')
@monitor_performance
def get_data(request):
    # Your route logic
    pass
```

### Health Checks

```python
@app.route('/health')
def health_check(request):
    """Health check endpoint for load balancers."""
    try:
        # Check database connection
        app.database.execute('SELECT 1')
        
        # Check Redis connection (if using)
        # redis_client.ping()
        
        return Response.json({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': app.version
        })
    except Exception as e:
        return Response.json({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
```

### Logging Configuration

```python
# logging_config.py
import logging
import logging.handlers
import os

def setup_logging(app):
    """Set up production logging."""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', '/var/log/wolfpy/app.log')
    
    # Create log directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
    
    # Set up application logger
    app_logger = logging.getLogger('wolfpy')
    app_logger.setLevel(getattr(logging, log_level))
```

## 🔒 Security Best Practices

### SSL/TLS Configuration

```bash
# Get SSL certificate with Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Security Headers

```python
# security_middleware.py
class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        def new_start_response(status, response_headers):
            # Add security headers
            security_headers = [
                ('X-Frame-Options', 'DENY'),
                ('X-Content-Type-Options', 'nosniff'),
                ('X-XSS-Protection', '1; mode=block'),
                ('Strict-Transport-Security', 'max-age=31536000; includeSubDomains'),
                ('Referrer-Policy', 'strict-origin-when-cross-origin'),
                ('Content-Security-Policy', "default-src 'self'")
            ]
            response_headers.extend(security_headers)
            return start_response(status, response_headers)
        
        return self.app(environ, new_start_response)

# Apply middleware
app.add_middleware(SecurityMiddleware)
```

## 🚀 Performance Optimization

### Gunicorn Configuration

```python
# gunicorn.conf.py
import multiprocessing

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

### Caching

```python
# Enable Redis caching
app = WolfPy(
    cache_url='redis://localhost:6379/0',
    cache_default_timeout=300
)

@app.route('/api/data')
@app.cache.cached(timeout=60)
def get_data(request):
    # Expensive operation
    return expensive_computation()
```

---

**Your WolfPy application is now ready for production! 🚀**
