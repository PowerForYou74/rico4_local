#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Rico System Deploy gestartet..."

# Change to project directory
cd /opt/rico4

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📝 .env.local wird erstellt..."
    cp env.template .env.local
    echo "⚠️  Bitte .env.local mit echten Werten konfigurieren!"
fi

# Pull latest images
echo "📦 Docker Images werden aktualisiert..."
docker-compose pull || true

# Build images
echo "🔨 Docker Images werden gebaut..."
docker-compose build --pull

# Stop existing containers
echo "⏹️  Bestehende Container werden gestoppt..."
docker-compose down --remove-orphans || true

# Start services
echo "▶️  Services werden gestartet..."
docker-compose up -d

# Wait for services to start
echo "⏳ Warte auf Service-Start..."
sleep 30

# Health checks
echo "🏥 Health Checks werden durchgeführt..."

# Backend health check
echo "🔍 Backend Health Check..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend ist gesund"
else
    echo "❌ Backend Health Check fehlgeschlagen"
    docker-compose logs backend
    exit 1
fi

# Frontend health check
echo "🔍 Frontend Health Check..."
if curl -f http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Frontend ist gesund"
else
    echo "❌ Frontend Health Check fehlgeschlagen"
    docker-compose logs frontend
    exit 1
fi

# n8n health check
echo "🔍 n8n Health Check..."
if curl -f http://localhost:5678/healthz > /dev/null 2>&1; then
    echo "✅ n8n ist gesund"
else
    echo "⚠️  n8n Health Check fehlgeschlagen (kann normal sein)"
fi

# Show container status
echo "📊 Container Status:"
docker-compose ps

echo "✅ Deploy abgeschlossen!"
echo "🌐 Services verfügbar:"
echo "   - Backend: http://localhost:8000"
echo "   - Frontend: http://localhost:3000"
echo "   - n8n: http://localhost:5678"
echo "   - Nginx: http://localhost"
