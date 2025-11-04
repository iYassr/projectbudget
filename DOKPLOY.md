# Dokploy Deployment Guide

This guide will help you deploy the Expense Tracker application to your Dokploy instance.

## Prerequisites

- A running Dokploy instance
- Your Dokploy API key
- Git repository access (GitHub, GitLab, Bitbucket, or custom Git)

## Quick Deployment

### Option 1: Deploy via Dokploy Web UI

1. **Login to Dokploy Dashboard**
   - Navigate to your Dokploy instance URL
   - Login with your credentials

2. **Create New Project** (if needed)
   - Click "Projects" → "New Project"
   - Enter project name and description

3. **Add Docker Compose Application**
   - Select your project
   - Click "Add Service" → "Docker Compose"
   - Enter application name: `expense-tracker`

4. **Configure Repository**
   - **Source Type**: Choose your Git provider (GitHub/GitLab/Bitbucket)
   - **Repository URL**: `https://github.com/iYassr/projectbudget.git`
   - **Branch**: `master`
   - **Compose File Path**: `docker-compose.yml` (default)

5. **Configure Environment Variables**
   Add the following environment variables:
   ```bash
   OPENAI_API_KEY=sk-your_openai_api_key
   ANTHROPIC_API_KEY=sk-ant-your_anthropic_api_key
   DOMAIN=your-domain.com
   ```

6. **Configure Domain** (Optional)
   - In the application settings, configure your domain
   - The app will be accessible at `expense-tracker.your-domain.com`
   - Dokploy will automatically provision SSL via Let's Encrypt

7. **Deploy**
   - Click "Deploy" button
   - Monitor deployment logs in real-time
   - Wait for deployment to complete

8. **Access Your Application**
   - If domain configured: `https://expense-tracker.your-domain.com`
   - If using port: `http://your-server-ip:8501`

---

### Option 2: Deploy via Dokploy API

#### 1. Set Environment Variables

```bash
export DOKPLOY_URL="https://your-dokploy-instance.com"
export DOKPLOY_API_KEY="my_appUbBBRaIYitusodZqihGWDSPTYuHqcCrEBTLCSWSfNRQoZYrAntZuNPtkQeWhygDV"
export PROJECT_ID="your-project-id"
```

#### 2. Create Compose Application

```bash
curl -X POST "${DOKPLOY_URL}/api/compose.create" \
  -H "Authorization: Bearer ${DOKPLOY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "expense-tracker",
    "projectId": "'"${PROJECT_ID}"'",
    "description": "Monthly Expense Tracker with AI categorization",
    "composeType": "docker-compose",
    "appName": "expense-tracker"
  }'
```

Save the returned `composeId` for next steps.

#### 3. Update Compose Configuration

```bash
export COMPOSE_ID="your-compose-id-from-above"

curl -X POST "${DOKPLOY_URL}/api/compose.update" \
  -H "Authorization: Bearer ${DOKPLOY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "composeId": "'"${COMPOSE_ID}"'",
    "sourceType": "github",
    "repository": "projectbudget",
    "owner": "iYassr",
    "branch": "master",
    "autoDeploy": true,
    "composeFile": "docker-compose.yml",
    "env": "OPENAI_API_KEY=sk-your-key\nANTHROPIC_API_KEY=sk-ant-your-key\nDOMAIN=your-domain.com"
  }'
```

#### 4. Deploy Application

```bash
curl -X POST "${DOKPLOY_URL}/api/compose.deploy" \
  -H "Authorization: Bearer ${DOKPLOY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "composeId": "'"${COMPOSE_ID}"'"
  }'
```

#### 5. Check Deployment Status

```bash
curl -X GET "${DOKPLOY_URL}/api/compose.one?composeId=${COMPOSE_ID}" \
  -H "Authorization: Bearer ${DOKPLOY_API_KEY}"
```

---

## Docker Compose Configuration

The `docker-compose.yml` has been optimized for Dokploy with:

### 1. Persistent Volumes
Uses `../files/` directory structure for data persistence:
```yaml
volumes:
  - ../files/data:/app/data
  - ../files/reports:/app/reports
  - ../files/logs:/app/logs
```

This ensures data persists between deployments.

### 2. Dokploy Network
```yaml
networks:
  - dokploy-network  # External network for Traefik
  - expense-tracker-network  # Internal network
```

### 3. Traefik Labels
Automatic reverse proxy configuration:
```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.expense-tracker.rule=Host(`expense-tracker.${DOMAIN}`)"
  - "traefik.http.services.expense-tracker.loadbalancer.server.port=8501"
```

---

## Pre-Deployment Setup

### Prepare Initial Files

Before first deployment, you may want to seed the files directory:

```bash
# Create files directory structure
mkdir -p ../files/{data,reports,logs,config}

# Copy initial configuration
cp -r config/* ../files/config/
cp merchant_cache.json ../files/

# Initialize empty database (optional - will be created automatically)
touch ../files/data/expenses.db
```

---

## Post-Deployment Tasks

### 1. Verify Deployment
```bash
# Check if service is running
curl https://expense-tracker.your-domain.com/_stcore/health

# Expected response: {"status": "ok"}
```

### 2. Upload Initial Data (Optional)
If you have existing SMS export:

```bash
# Via Dokploy exec
docker exec expense-tracker-dashboard python3 extract_from_txt_export.py /app/data/messages.txt
```

### 3. Enable Webhooks (Optional)
For automatic deployments on git push:
1. Go to your Dokploy compose application settings
2. Copy the webhook URL
3. Add it to your GitHub/GitLab repository webhooks

---

## Monitoring & Maintenance

### View Logs
```bash
# Dashboard logs
docker logs expense-tracker-dashboard -f

# Or via Dokploy UI
# Navigate to: Compose → expense-tracker → Logs
```

### Create Backup
```bash
# Via Dokploy exec
docker compose run --rm backup
```

### Redeploy Application
```bash
# Via API
curl -X POST "${DOKPLOY_URL}/api/compose.redeploy" \
  -H "Authorization: Bearer ${DOKPLOY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "composeId": "'"${COMPOSE_ID}"'"
  }'
```

### Stop Application
```bash
# Via API
curl -X POST "${DOKPLOY_URL}/api/compose.stop" \
  -H "Authorization: Bearer ${DOKPLOY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "composeId": "'"${COMPOSE_ID}"'"
  }'
```

---

## Troubleshooting

### Application Not Accessible

**Check service status:**
```bash
docker ps | grep expense-tracker
```

**Check Traefik routing:**
```bash
docker logs traefik | grep expense-tracker
```

**Verify domain DNS:**
```bash
nslookup expense-tracker.your-domain.com
```

### Database Issues

**Check database file permissions:**
```bash
docker exec expense-tracker-dashboard ls -la /app/data/
```

**Reinitialize database:**
```bash
docker exec expense-tracker-dashboard python3 -c "from src.database import ExpenseDatabase; ExpenseDatabase('/app/data/expenses.db')"
```

### Volume Not Persisting

Ensure you're using `../files/` paths in docker-compose.yml:
```yaml
# ✅ Correct (persists)
- ../files/data:/app/data

# ❌ Wrong (gets cleaned up)
- ./data:/app/data
```

### Build Failures

**Clear build cache:**
```bash
# Via Dokploy UI: Compose → expense-tracker → Settings → Clean Build Cache
```

**Check build logs:**
```bash
# Via Dokploy UI: Compose → expense-tracker → Deployments → Latest → Logs
```

---

## Environment Variables Reference

### Required
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` - For AI categorization (optional but recommended)

### Optional
- `DOMAIN` - Your domain name for Traefik routing
- `GOOGLE_SHEETS_CREDENTIALS` - Path to Google Sheets credentials
- `GOOGLE_SHEET_ID` - Google Sheet ID for exports
- `MESSAGES_DB_PATH` - iPhone Messages database path (for Mac local extraction)

---

## Optional Services

### Enable Scheduler (Monthly Processing)
To enable automated monthly expense processing:

1. Edit compose configuration
2. Enable profile: `with-scheduler`
3. Redeploy

### Enable Backup Service
For regular database backups:

1. Edit compose configuration
2. Enable profile: `backup`
3. Configure backup schedule (via cron or Dokploy scheduler)

---

## Security Considerations

### 1. Protect API Keys
Never commit `.env` file to git:
```bash
# Already in .gitignore
echo ".env" >> .gitignore
```

### 2. Use Secrets (Recommended for Production)
Instead of environment variables, use Dokploy secrets:
1. Navigate to Project → Secrets
2. Add secrets: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
3. Reference in compose: `${OPENAI_API_KEY}`

### 3. Restrict Access
Configure authentication via Traefik middleware:
```yaml
labels:
  - "traefik.http.routers.expense-tracker.middlewares=auth"
  - "traefik.http.middlewares.auth.basicauth.users=user:$$apr1$$..."
```

### 4. Regular Backups
Schedule automated backups:
```bash
# Via cron on Dokploy server
0 2 * * * docker compose run --rm -f /path/to/compose/docker-compose.yml backup
```

---

## Scaling & Performance

### Vertical Scaling
Increase container resources via Dokploy:
1. Compose → expense-tracker → Settings → Resources
2. Adjust CPU/Memory limits

### Horizontal Scaling
Not recommended for this application (SQLite database limitation)

### Database Optimization
For better performance with large datasets:
```bash
docker exec expense-tracker-dashboard sqlite3 /app/data/expenses.db "VACUUM;"
docker exec expense-tracker-dashboard sqlite3 /app/data/expenses.db "ANALYZE;"
```

---

## Support & Resources

- **Dokploy Documentation**: https://docs.dokploy.com
- **Expense Tracker Docs**: See README.md, DOCKER.md
- **Issue Tracking**: https://github.com/iYassr/projectbudget/issues

---

## Quick Reference Commands

```bash
# Deploy
curl -X POST "${DOKPLOY_URL}/api/compose.deploy" -H "Authorization: Bearer ${DOKPLOY_API_KEY}" -d '{"composeId": "xxx"}'

# Stop
curl -X POST "${DOKPLOY_URL}/api/compose.stop" -H "Authorization: Bearer ${DOKPLOY_API_KEY}" -d '{"composeId": "xxx"}'

# Redeploy
curl -X POST "${DOKPLOY_URL}/api/compose.redeploy" -H "Authorization: Bearer ${DOKPLOY_API_KEY}" -d '{"composeId": "xxx"}'

# View status
curl -X GET "${DOKPLOY_URL}/api/compose.one?composeId=xxx" -H "Authorization: Bearer ${DOKPLOY_API_KEY}"

# Exec into container
docker exec -it expense-tracker-dashboard bash

# View logs
docker logs expense-tracker-dashboard -f

# Backup database
docker compose run --rm backup

# Extract from TXT
docker compose run --rm dashboard extract /app/data/messages.txt
```

---

**Ready to deploy!** 🚀

Choose your preferred method above and follow the steps to deploy your expense tracker to Dokploy.
