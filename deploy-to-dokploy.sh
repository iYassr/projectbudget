#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Dokploy Deployment Script ===${NC}"
echo ""

# Check if required environment variables are set
if [ -z "$DOKPLOY_URL" ]; then
    echo -e "${YELLOW}DOKPLOY_URL not set${NC}"
    read -p "Enter your Dokploy instance URL (e.g., https://dokploy.yourdomain.com): " DOKPLOY_URL
    export DOKPLOY_URL
fi

if [ -z "$DOKPLOY_API_KEY" ]; then
    echo -e "${YELLOW}DOKPLOY_API_KEY not set${NC}"
    read -p "Enter your Dokploy API key: " DOKPLOY_API_KEY
    export DOKPLOY_API_KEY
fi

if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}PROJECT_ID not set${NC}"
    read -p "Enter your Dokploy project ID: " PROJECT_ID
    export PROJECT_ID
fi

echo ""
echo -e "${BLUE}Configuration:${NC}"
echo "  Dokploy URL: $DOKPLOY_URL"
echo "  API Key: ${DOKPLOY_API_KEY:0:10}..."
echo "  Project ID: $PROJECT_ID"
echo ""

# Ask for confirmation
read -p "Proceed with deployment? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}Deployment cancelled${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Step 1: Creating compose application...${NC}"

# Create compose application
RESPONSE=$(curl -s -X POST "${DOKPLOY_URL}/api/compose.create" \
  -H "Authorization: Bearer ${DOKPLOY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "expense-tracker",
    "projectId": "'"${PROJECT_ID}"'",
    "description": "Monthly Expense Tracker with AI categorization and Streamlit dashboard",
    "composeType": "docker-compose",
    "appName": "expense-tracker"
  }')

# Extract composeId from response
COMPOSE_ID=$(echo $RESPONSE | grep -o '"composeId":"[^"]*' | cut -d'"' -f4)

if [ -z "$COMPOSE_ID" ]; then
    echo -e "${RED}Failed to create compose application${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Compose application created${NC}"
echo "  Compose ID: $COMPOSE_ID"
echo ""

# Save compose ID for future use
echo "export COMPOSE_ID=$COMPOSE_ID" > .dokploy-env
echo -e "${BLUE}Compose ID saved to .dokploy-env${NC}"

echo ""
echo -e "${GREEN}Step 2: Configuring repository and settings...${NC}"

# Get environment variables
echo ""
echo -e "${YELLOW}Environment Variables Setup:${NC}"
read -p "Enter your OPENAI_API_KEY (or press Enter to skip): " OPENAI_KEY
read -p "Enter your ANTHROPIC_API_KEY (or press Enter to skip): " ANTHROPIC_KEY
read -p "Enter your domain (e.g., yourdomain.com): " DOMAIN

# Build environment string
ENV_STRING=""
if [ ! -z "$OPENAI_KEY" ]; then
    ENV_STRING="${ENV_STRING}OPENAI_API_KEY=${OPENAI_KEY}\n"
fi
if [ ! -z "$ANTHROPIC_KEY" ]; then
    ENV_STRING="${ENV_STRING}ANTHROPIC_API_KEY=${ANTHROPIC_KEY}\n"
fi
if [ ! -z "$DOMAIN" ]; then
    ENV_STRING="${ENV_STRING}DOMAIN=${DOMAIN}\n"
fi
ENV_STRING="${ENV_STRING}PYTHONUNBUFFERED=1"

# Update compose configuration
curl -s -X POST "${DOKPLOY_URL}/api/compose.update" \
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
    "env": "'"${ENV_STRING}"'"
  }' > /dev/null

echo -e "${GREEN}✓ Repository and environment configured${NC}"
echo ""

echo -e "${GREEN}Step 3: Deploying application...${NC}"

# Deploy application
DEPLOY_RESPONSE=$(curl -s -X POST "${DOKPLOY_URL}/api/compose.deploy" \
  -H "Authorization: Bearer ${DOKPLOY_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "composeId": "'"${COMPOSE_ID}"'"
  }')

echo -e "${GREEN}✓ Deployment initiated${NC}"
echo ""

echo -e "${GREEN}=== Deployment Summary ===${NC}"
echo ""
echo "  Application Name: expense-tracker"
echo "  Compose ID: $COMPOSE_ID"
echo "  Repository: https://github.com/iYassr/projectbudget"
echo "  Branch: master"
echo ""

if [ ! -z "$DOMAIN" ]; then
    echo "  Dashboard URL: https://expense-tracker.${DOMAIN}"
else
    echo "  Dashboard URL: Check Dokploy UI for assigned URL"
fi

echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Monitor deployment in Dokploy UI: ${DOKPLOY_URL}"
echo "  2. Check logs: Compose → expense-tracker → Logs"
echo "  3. View deployment progress: Compose → expense-tracker → Deployments"
echo ""

echo -e "${YELLOW}Useful Commands:${NC}"
echo "  # Check status"
echo "  curl -X GET '${DOKPLOY_URL}/api/compose.one?composeId=${COMPOSE_ID}' -H 'Authorization: Bearer ${DOKPLOY_API_KEY}'"
echo ""
echo "  # Redeploy"
echo "  curl -X POST '${DOKPLOY_URL}/api/compose.redeploy' -H 'Authorization: Bearer ${DOKPLOY_API_KEY}' -d '{\"composeId\": \"${COMPOSE_ID}\"}'"
echo ""
echo "  # Stop"
echo "  curl -X POST '${DOKPLOY_URL}/api/compose.stop' -H 'Authorization: Bearer ${DOKPLOY_API_KEY}' -d '{\"composeId\": \"${COMPOSE_ID}\"}'"
echo ""

echo -e "${GREEN}Deployment script completed! 🚀${NC}"
echo ""
echo -e "${YELLOW}Note: The deployment may take a few minutes to complete.${NC}"
echo -e "${YELLOW}Monitor progress in your Dokploy dashboard.${NC}"
