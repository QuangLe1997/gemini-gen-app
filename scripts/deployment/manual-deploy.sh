#!/bin/bash

# Manual deployment script for Gemini Gen App
# This script deploys the application to the server

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Server configuration
SERVER="54.248.140.63"
SSH_PORT="22"
USER="quanglv"
REMOTE_DIR="/home/quanglv/gemini-gen-app"

echo -e "${BLUE}=== Manual Deployment to $SERVER ===${NC}"
echo

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}📂 Project root: $PROJECT_ROOT${NC}"

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
    echo '⚠️  Cannot connect to GitHub. Trying with DNS...'
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
        git clone https://github.com/QuangLe1997/gemini-gen-app.git \$(basename $REMOTE_DIR)
    else
        echo '❌ Cannot reach GitHub for cloning. Server needs internet access.'
        exit 1
    fi
    cd $REMOTE_DIR
elif [ ! -d $REMOTE_DIR/.git ]; then
    echo '⚠️  Directory exists but not a git repository. Re-cloning...'
    rm -rf $REMOTE_DIR
    mkdir -p $REMOTE_DIR
    cd \$(dirname $REMOTE_DIR)
    
    # Test internet connectivity for git clone
    if ping -c 1 github.com &> /dev/null; then
        echo '🌐 Cloning from GitHub...'
        git clone https://github.com/QuangLe1997/gemini-gen-app.git \$(basename $REMOTE_DIR)
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
        echo '📥 Pulling latest code...'
        if ping -c 1 github.com &> /dev/null; then
            git pull origin main
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
            git checkout -b main origin/main
        else
            echo '⚠️  Cannot reach GitHub. Using existing files without git.'
        fi
    fi
fi

echo '📝 Creating .env file...'
cat > .env << 'EOF'
# Auto-generated environment file
# Generated at: \$(date -u +%Y-%m-%dT%H:%M:%SZ)

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000
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
fi

if ! command -v docker-compose &> /dev/null; then
    echo '📥 Docker Compose not found. Installing Docker Compose...'
    sudo curl -L \"https://github.com/docker/compose/releases/download/v2.24.0/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo '✅ Docker Compose installed successfully'
fi

echo '🛑 Stopping existing containers...'
docker-compose down || echo 'No containers to stop'

echo '🏗️  Building and starting containers...'
docker-compose pull
docker-compose build --no-cache
docker-compose up -d

echo '⏳ Waiting for services to initialize...'
sleep 10

echo '🔍 Checking container status...'
docker-compose ps

echo '📋 Showing container logs...'
docker-compose logs --tail=50

echo '🧹 Cleaning up old images...'
docker image prune -f || true

echo '🎉 Deployment completed!'
echo '🌐 Services should be available at:'
echo '  - Web App: http://$SERVER:5000'
echo '  - Nginx: http://$SERVER'
"

echo
echo -e "${BLUE}=== Post-deployment Health Checks ===${NC}"

echo -e "${YELLOW}⏳ Waiting 10 seconds for services to be ready...${NC}"
sleep 10

echo -e "${YELLOW}🔍 Checking Web App health...${NC}"
if curl -f -s "http://$SERVER:5000" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Web App is healthy!${NC}"
else
    echo -e "${YELLOW}⚠️  Web App not ready yet, may need more time${NC}"
fi

echo -e "${YELLOW}🔍 Checking Nginx...${NC}"
if curl -f -s "http://$SERVER" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Nginx is accessible!${NC}"
else
    echo -e "${YELLOW}⚠️  Nginx not ready yet, may need more time${NC}"
fi

echo
echo -e "${GREEN}=== Manual Deployment Complete! ===${NC}"
echo
echo -e "${BLUE}📊 Service URLs:${NC}"
echo "  🔗 Web App: http://$SERVER:5000"
echo "  🔗 Nginx: http://$SERVER"
echo
echo -e "${YELLOW}💡 Tips:${NC}"
echo "  - SSH to server: ssh -p $SSH_PORT $USER@$SERVER"
echo "  - View logs: docker-compose logs -f"
echo "  - Restart services: docker-compose restart"
echo "  - Stop services: docker-compose down"