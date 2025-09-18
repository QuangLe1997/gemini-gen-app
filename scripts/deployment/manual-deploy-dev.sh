#!/bin/bash

# Manual deployment script for Gemini Gen App - DEV Environment
# This script deploys the application to the development server

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Development Server configuration
SERVER="54.248.140.63"
SSH_PORT="22"
USER="quanglv"
REMOTE_DIR="/home/quanglv/dev-gemini-gen-app"
BRANCH="main"  # Can be changed to develop branch

echo -e "${BLUE}=== Manual Deployment to DEV Server $SERVER ===${NC}"
echo

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/deployment/.env.dev"

echo -e "${BLUE}📂 Project root: $PROJECT_ROOT${NC}"
echo -e "${BLUE}📄 Looking for: $ENV_FILE${NC}"

# Check if .env.dev file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}⚠️  $ENV_FILE file not found!${NC}"
    echo "Creating default .env.dev file..."
    
    mkdir -p "$PROJECT_ROOT/deployment"
    cat > "$ENV_FILE" << 'EOF'
# Development Environment Configuration
# Generated at deployment time

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production

# API Configuration
API_HOST=0.0.0.0
API_PORT=5001
DEBUG=true

# Gemini API (add your key here)
GEMINI_API_KEY=${GEMINI_API_KEY:-}

# File Upload Settings
MAX_CONTENT_LENGTH=104857600
UPLOAD_FOLDER=/app/uploads
OUTPUT_FOLDER=/app/outputs

# CORS Settings
CORS_ORIGINS=*

# Rate Limiting
RATE_LIMIT_ENABLED=false
EOF
    echo -e "${GREEN}✅ Created default .env.dev file${NC}"
fi

echo -e "${YELLOW}📄 Loading environment variables from $ENV_FILE...${NC}"

# Read .env.dev file and export variables
set -a  # automatically export all variables
source "$ENV_FILE"
set +a

echo -e "${YELLOW}🔍 Testing server connectivity...${NC}"
if ssh -p $SSH_PORT -o ConnectTimeout=5 $USER@$SERVER "echo 'Connected'" &> /dev/null; then
    echo -e "${GREEN}✅ Server is accessible${NC}"
else
    echo -e "${RED}❌ Cannot connect to server${NC}"
    echo "Please check:"
    echo "  - Server IP: $SERVER"
    echo "  - SSH Port: $SSH_PORT"
    echo "  - Username: $USER"
    echo "  - Your SSH key is configured"
    exit 1
fi

echo -e "${YELLOW}🚀 Triggering deployment via SSH...${NC}"

ssh -p $SSH_PORT $USER@$SERVER "
set -e

echo '🌐 Checking network connectivity...'
if ! ping -c 1 8.8.8.8 &> /dev/null; then
    echo '❌ No internet connection detected'
    exit 1
fi

echo '🔍 Testing GitHub connectivity...'
if ! nc -zv github.com 443 2>&1 | grep -q 'succeeded'; then
    echo '⚠️  Cannot connect to GitHub. Trying with DNS fix...'
    echo '8.8.8.8 google-public-dns-a.google.com' | sudo tee -a /etc/hosts > /dev/null
    echo '140.82.112.3 github.com' | sudo tee -a /etc/hosts > /dev/null
fi

echo '📂 Checking project directory...'
if [ ! -d $REMOTE_DIR ]; then
    echo '📥 Project not found. Creating directory and cloning repository...'
    mkdir -p $REMOTE_DIR
    cd \$(dirname $REMOTE_DIR)
    
    # Test internet connectivity for git clone
    if ping -c 1 github.com &> /dev/null; then
        echo '🌐 Cloning from GitHub...'
        # Fix SSL certificate verification issue if needed
        git -c http.sslVerify=false clone https://github.com/QuangLe1997/gemini-gen-app.git \$(basename $REMOTE_DIR)
    else
        echo '❌ Cannot reach GitHub for cloning. Server needs internet access.'
        exit 1
    fi
    cd $REMOTE_DIR
elif [ ! -d $REMOTE_DIR/.git ]; then
    echo '⚠️  Directory exists but not a git repository. Re-cloning...'
    sudo rm -rf $REMOTE_DIR
    mkdir -p $REMOTE_DIR
    cd \$(dirname $REMOTE_DIR)
    
    # Test internet connectivity for git clone
    if ping -c 1 github.com &> /dev/null; then
        echo '🌐 Cloning from GitHub...'
        # Fix SSL certificate verification issue if needed
        git -c http.sslVerify=false clone https://github.com/QuangLe1997/gemini-gen-app.git \$(basename $REMOTE_DIR)
    else
        echo '❌ Cannot reach GitHub for cloning. Server needs internet access.'
        exit 1
    fi
    cd $REMOTE_DIR
else
    echo '📂 Navigating to existing repository...'
    cd $REMOTE_DIR
    
    # Check if we can pull (git repository exists and has remote)
    if [ -d .git ] && git remote get-url origin &> /dev/null; then
        echo '📥 Pulling latest code from $BRANCH branch...'
        if ping -c 1 github.com &> /dev/null; then
            # Fix SSL certificate verification issue if needed
            git -c http.sslVerify=false fetch origin
            git checkout $BRANCH || git checkout -b $BRANCH origin/$BRANCH
            git -c http.sslVerify=false pull origin $BRANCH
        else
            echo '⚠️  Cannot reach GitHub for pulling. Using existing code.'
        fi
    else
        echo '⚠️  Git repository corrupted or no remote configured.'
        echo '🔧 Re-initializing git repository...'
        rm -rf .git
        git init
        if ping -c 1 github.com &> /dev/null; then
            git remote add origin https://github.com/QuangLe1997/gemini-gen-app.git
            git fetch origin
            git checkout -b $BRANCH origin/$BRANCH
        else
            echo '⚠️  Cannot reach GitHub. Using existing files without git.'
        fi
    fi
fi

echo '📝 Creating .env file for DEV environment...'
cat > .env << 'EOF'
# Auto-generated environment file for DEV
# Generated at: \$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Flask Configuration
FLASK_ENV=$FLASK_ENV
FLASK_DEBUG=$FLASK_DEBUG
SECRET_KEY=$SECRET_KEY

# API Configuration
API_HOST=$API_HOST
API_PORT=$API_PORT
DEBUG=$DEBUG

# Gemini API
GEMINI_API_KEY=$GEMINI_API_KEY

# File Upload Settings
MAX_CONTENT_LENGTH=$MAX_CONTENT_LENGTH
UPLOAD_FOLDER=$UPLOAD_FOLDER
OUTPUT_FOLDER=$OUTPUT_FOLDER

# CORS Settings
CORS_ORIGINS=$CORS_ORIGINS

# Rate Limiting
RATE_LIMIT_ENABLED=$RATE_LIMIT_ENABLED
EOF

echo '✅ Environment file created'

echo '🔍 Checking Docker installation...'
if ! command -v docker &> /dev/null; then
    echo '📥 Docker not found. Installing Docker...'
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker \$USER
    rm get-docker.sh
    echo '✅ Docker installed successfully'
    echo '⚠️  You may need to log out and back in for docker group changes'
fi

if ! command -v docker-compose &> /dev/null; then
    echo '📥 Docker Compose not found. Installing Docker Compose...'
    sudo curl -L \"https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo '✅ Docker Compose installed successfully'
fi

echo '📝 Creating docker-compose.dev.yml for development...'
cat > docker-compose.dev.yml << 'EOFD'
version: '3.8'

services:
  gemini-gen-app-dev:
    build: 
      context: .
      dockerfile: Dockerfile
    container_name: gemini-gen-app-dev
    ports:
      - \"5001:5000\"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./templates:/app/templates
      - .:/app  # Mount entire app for hot reload
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=true
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    networks:
      - gemini-dev-net
    command: python -m flask run --host=0.0.0.0 --port=5000 --reload

  nginx-dev:
    image: nginx:alpine
    container_name: gemini-nginx-dev
    ports:
      - \"8080:80\"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - gemini-gen-app-dev
    restart: unless-stopped
    networks:
      - gemini-dev-net

networks:
  gemini-dev-net:
    driver: bridge
EOFD

echo '✅ Development docker-compose file created'

echo '🛑 Stopping existing DEV containers...'
docker-compose -f docker-compose.dev.yml down || echo 'No containers to stop'

echo '🧹 Cleaning up old containers and images...'
docker container prune -f || true
docker image prune -f || true

echo '🏗️  Building and starting DEV containers...'
docker-compose -f docker-compose.dev.yml pull
docker-compose -f docker-compose.dev.yml build --no-cache
docker-compose -f docker-compose.dev.yml up -d

echo '⏳ Waiting for services to initialize...'
sleep 15

echo '🔍 Checking container status...'
docker-compose -f docker-compose.dev.yml ps

echo '📋 Showing container logs (last 100 lines)...'
docker-compose -f docker-compose.dev.yml logs --tail=100

echo '🎉 DEV Deployment completed!'
echo '🌐 Services should be available at:'
echo '  - Web App (Dev): http://$SERVER:5001'
echo '  - Nginx (Dev): http://$SERVER:8080'
echo ''
echo '🔧 Development Features:'
echo '  - Hot reload enabled'
echo '  - Debug mode active'
echo '  - Full error traces'
"

echo
echo -e "${BLUE}=== Post-deployment Health Checks ===${NC}"

echo -e "${YELLOW}⏳ Waiting 15 seconds for services to be ready...${NC}"
sleep 15

echo -e "${YELLOW}🔍 Checking DEV Web App health...${NC}"
if curl -f -s "http://$SERVER:5001" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ DEV Web App is healthy!${NC}"
    echo -e "${BLUE}   Response preview:${NC}"
    curl -s "http://$SERVER:5001" | head -n 5
else
    echo -e "${RED}❌ DEV Web App not responding${NC}"
    echo "Checking Docker logs..."
    ssh -p $SSH_PORT $USER@$SERVER "cd $REMOTE_DIR && docker-compose -f docker-compose.dev.yml logs --tail=20 gemini-gen-app-dev"
fi

echo -e "${YELLOW}🔍 Checking DEV Nginx...${NC}"
if curl -f -s "http://$SERVER:8080" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ DEV Nginx is accessible!${NC}"
else
    echo -e "${YELLOW}⚠️  DEV Nginx not ready yet${NC}"
fi

echo
echo -e "${GREEN}=== DEV Deployment Complete! ===${NC}"
echo
echo -e "${BLUE}📊 DEV Service URLs:${NC}"
echo "  🔗 Web App (Dev): http://$SERVER:5001"
echo "  🔗 Nginx (Dev): http://$SERVER:8080"
echo
echo -e "${YELLOW}💡 Useful Commands:${NC}"
echo "  📝 View logs: ssh -p $SSH_PORT $USER@$SERVER 'cd $REMOTE_DIR && docker-compose -f docker-compose.dev.yml logs -f'"
echo "  🔄 Restart: ssh -p $SSH_PORT $USER@$SERVER 'cd $REMOTE_DIR && docker-compose -f docker-compose.dev.yml restart'"
echo "  🛑 Stop: ssh -p $SSH_PORT $USER@$SERVER 'cd $REMOTE_DIR && docker-compose -f docker-compose.dev.yml down'"
echo "  📊 Status: ssh -p $SSH_PORT $USER@$SERVER 'cd $REMOTE_DIR && docker-compose -f docker-compose.dev.yml ps'"
echo
echo -e "${BLUE}🔧 Development Notes:${NC}"
echo "  - Hot reload is enabled - code changes auto-reload"
echo "  - Debug mode active - detailed error messages"
echo "  - Mounted volumes for live code updates"
echo "  - Separate ports to avoid conflicts (5001, 8080)"