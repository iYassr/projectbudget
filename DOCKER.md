# Docker Setup Guide

## 🐳 Quick Start

### Prerequisites
- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Docker Compose installed (included with Docker Desktop)

### 1. Clone and Setup

```bash
git clone <your-repo>
cd projectbudget

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

### 2. Start the Dashboard

```bash
# Build and start
docker compose up dashboard

# Or run in background
docker compose up -d dashboard
```

Dashboard will be available at: **http://localhost:8501**

---

## 📋 Available Commands

### Dashboard
```bash
# Start dashboard
docker compose up dashboard

# Start in background (detached)
docker compose up -d dashboard

# View logs
docker compose logs -f dashboard

# Stop
docker compose down
```

### Extract Expenses from TXT File
```bash
# Extract from messages.txt
docker compose run --rm dashboard extract /app/data/messages.txt

# With volume mount
docker compose run --rm -v $(pwd)/messages.txt:/app/messages.txt dashboard extract /app/messages.txt
```

### Recategorize Expenses
```bash
# Dry run (preview changes)
docker compose run --rm dashboard recategorize

# Apply changes
docker compose run --rm dashboard recategorize --apply

# With AI
docker compose run --rm dashboard recategorize --use-ai --apply
```

### Backup Database
```bash
# Create backup
docker compose run --rm dashboard backup

# Backups are stored in ./backups/
```

### Interactive Shell
```bash
# Bash shell
docker compose run --rm dashboard bash

# Python shell
docker compose run --rm dashboard python
```

### Run Tests
```bash
docker compose run --rm dashboard test
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file with:

```bash
# Required for AI categorization (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Optional
GOOGLE_SHEETS_CREDENTIALS=/app/credentials.json
GOOGLE_SHEET_ID=your_sheet_id
```

### Volume Mounts

Docker Compose automatically mounts:
- `./data` → Database storage
- `./reports` → Generated reports
- `./logs` → Application logs
- `./merchant_cache.json` → Merchant cache
- `./config` → Configuration files

---

## 🚀 Advanced Usage

### Run with Scheduler (Automatic Monthly Processing)

```bash
docker compose --profile with-scheduler up -d
```

This starts:
- Dashboard on port 8501
- Scheduler service (processes expenses on 1st of each month at 9 AM)

### Custom Docker Build

```bash
# Build specific image
docker build -t expense-tracker:latest .

# Build with custom Dockerfile
docker build -f Dockerfile.custom -t expense-tracker:custom .

# Build without cache
docker build --no-cache -t expense-tracker:latest .
```

### Run on Different Port

```bash
# Edit docker-compose.yml ports section:
ports:
  - "8080:8501"  # Access on http://localhost:8080
```

Or override via command line:

```bash
docker compose run --rm -p 8080:8501 dashboard
```

---

## 🔒 Production Deployment

### Using Docker Compose (Production)

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  dashboard:
    image: expense-tracker:latest
    restart: always
    ports:
      - "8501:8501"
    volumes:
      - data:/app/data
      - reports:/app/reports
    environment:
      - PYTHONUNBUFFERED=1
    env_file:
      - .env.production
    networks:
      - expense-tracker-network

volumes:
  data:
    driver: local
  reports:
    driver: local

networks:
  expense-tracker-network:
    driver: bridge
```

Start production:
```bash
docker compose -f docker-compose.prod.yml up -d
```

### Behind Nginx Reverse Proxy

```nginx
# /etc/nginx/sites-available/expense-tracker
server {
    listen 80;
    server_name expenses.yourdomain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### With SSL (Let's Encrypt)

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d expenses.yourdomain.com

# Auto-renewal is configured automatically
```

---

## 🛠️ Maintenance

### View Logs
```bash
# Real-time logs
docker compose logs -f dashboard

# Last 100 lines
docker compose logs --tail=100 dashboard

# Since specific time
docker compose logs --since 2025-01-01T00:00:00 dashboard
```

### Update Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker compose up -d --build dashboard
```

### Database Backup & Restore

**Backup:**
```bash
# Manual backup
docker compose run --rm dashboard backup

# Scheduled backup (cron)
0 2 * * * cd /path/to/projectbudget && docker compose run --rm dashboard backup
```

**Restore:**
```bash
# Copy backup to data directory
cp backups/expenses_backup_20250101_090000.db data/expenses.db

# Restart container
docker compose restart dashboard
```

### Clean Up
```bash
# Stop all containers
docker compose down

# Stop and remove volumes
docker compose down -v

# Remove unused images
docker image prune -a

# Full cleanup
docker system prune -a --volumes
```

---

## 🐛 Troubleshooting

### Container won't start
```bash
# Check logs
docker compose logs dashboard

# Check if port is already in use
lsof -i :8501

# Try different port
docker compose run --rm -p 8502:8501 dashboard
```

### Database locked error
```bash
# Stop all containers
docker compose down

# Remove lock
rm data/*.db-journal data/*.db-shm data/*.db-wal

# Restart
docker compose up dashboard
```

### Permission denied errors
```bash
# Fix ownership (Linux)
sudo chown -R $USER:$USER data/ reports/ logs/

# Or run with sudo (not recommended)
sudo docker compose up dashboard
```

### Cannot connect to dashboard
```bash
# Check if container is running
docker compose ps

# Check container network
docker compose exec dashboard curl http://localhost:8501/_stcore/health

# Check host firewall
sudo ufw allow 8501
```

### Out of disk space
```bash
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a --volumes

# Clean up old backups
rm -f backups/expenses_backup_*.db
```

---

## 📊 Resource Limits

Add resource limits to docker-compose.yml:

```yaml
services:
  dashboard:
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
```

---

## 🔐 Security Best Practices

1. **Don't commit .env file**
   ```bash
   # Already in .gitignore
   echo ".env" >> .gitignore
   ```

2. **Use secrets for production**
   ```yaml
   # docker-compose.yml
   secrets:
     openai_key:
       file: ./secrets/openai_key.txt

   services:
     dashboard:
       secrets:
         - openai_key
   ```

3. **Run as non-root user**
   ```dockerfile
   # Add to Dockerfile
   RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
   USER appuser
   ```

4. **Enable Docker security scanning**
   ```bash
   docker scan expense-tracker:latest
   ```

---

## 📱 Mobile Access

Access dashboard from mobile device on same network:

1. Find your computer's IP:
   ```bash
   # Linux/Mac
   ifconfig | grep "inet "

   # Windows
   ipconfig
   ```

2. Access from mobile browser:
   ```
   http://192.168.1.xxx:8501
   ```

---

## ☁️ Cloud Deployment

### Deploy to AWS ECS
```bash
# Build for multi-platform
docker buildx build --platform linux/amd64,linux/arm64 -t expense-tracker:latest .

# Push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag expense-tracker:latest <account>.dkr.ecr.us-east-1.amazonaws.com/expense-tracker:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/expense-tracker:latest
```

### Deploy to DigitalOcean
```bash
# Create droplet with Docker
doctl compute droplet create expense-tracker --image docker-20-04 --size s-1vcpu-1gb

# SSH and deploy
ssh root@<droplet-ip>
git clone <your-repo>
cd projectbudget
docker compose up -d
```

### Deploy to Google Cloud Run
```bash
# Build and push
gcloud builds submit --tag gcr.io/<project-id>/expense-tracker

# Deploy
gcloud run deploy expense-tracker \
  --image gcr.io/<project-id>/expense-tracker \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

## 💡 Tips

1. **Development mode with hot reload:**
   ```bash
   docker compose up dashboard
   # Streamlit auto-reloads on file changes
   ```

2. **Access database from host:**
   ```bash
   sqlite3 data/expenses.db
   ```

3. **Copy files from container:**
   ```bash
   docker cp expense-tracker-dashboard:/app/reports/january.xlsx ./
   ```

4. **Run one-off commands:**
   ```bash
   docker compose run --rm dashboard python -c "print('Hello')"
   ```

5. **Check container health:**
   ```bash
   docker compose exec dashboard curl http://localhost:8501/_stcore/health
   ```

---

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Streamlit Docker Deployment](https://docs.streamlit.io/knowledge-base/tutorials/deploy/docker)
- [SQLite in Docker](https://docs.docker.com/samples/sqlite/)

---

## 🤝 Contributing

When adding new features that require Docker changes:

1. Update Dockerfile if new dependencies needed
2. Update docker-compose.yml if new services needed
3. Update docker-entrypoint.sh if new commands needed
4. Update this DOCKER.md documentation
5. Test changes with `docker compose up --build`

---

## 📞 Support

If you encounter issues:
1. Check logs: `docker compose logs dashboard`
2. Review troubleshooting section above
3. Open an issue on GitHub with:
   - Docker version: `docker --version`
   - Docker Compose version: `docker-compose --version`
   - Error logs
   - Steps to reproduce
