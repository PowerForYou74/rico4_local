#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Rico System Server Bootstrap gestartet..."

# System Update
echo "📦 System wird aktualisiert..."
apt-get update -y
apt-get upgrade -y

# Install curl for health checks
echo "🔧 Curl wird installiert..."
apt-get install -y curl

# Docker Installation
echo "🐳 Docker wird installiert..."
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $USER
    rm get-docker.sh
    echo "✅ Docker installiert"
else
    echo "✅ Docker bereits installiert"
fi

# Docker Compose Installation
echo "🔧 Docker Compose wird installiert..."
if ! command -v docker-compose >/dev/null 2>&1; then
    apt-get install -y docker-compose
    echo "✅ Docker Compose installiert"
else
    echo "✅ Docker Compose bereits installiert"
fi

# Create project directory
echo "📁 Projektverzeichnis wird erstellt..."
mkdir -p /opt/rico4
mkdir -p /opt/rico4/n8n_data
mkdir -p /opt/rico4/data

# Set permissions
chown -R $USER:$USER /opt/rico4

echo "✅ Server Bootstrap abgeschlossen"
