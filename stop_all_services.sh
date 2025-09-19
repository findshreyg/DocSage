#!/bin/bash

# DocSage - Stop All Services Script

echo "🛑 Stopping DocSage Application..."

# Stop Node.js processes (frontend)
echo "🎨 Stopping Frontend..."
pkill -f "npm run dev" 2>/dev/null || echo "Frontend was not running"

# Stop Python/uvicorn processes (backend)
echo "📡 Stopping Backend Services..."
pkill -f "uvicorn" 2>/dev/null || echo "Backend services were not running"

# Stop Docker containers if they exist
if [ -f "backend/docker-compose.yml" ]; then
    echo "🐳 Stopping Docker containers..."
    cd backend && docker-compose down && cd ..
fi

# Kill any remaining processes on specific ports
echo "🔍 Cleaning up ports..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
lsof -ti:8002 | xargs kill -9 2>/dev/null || true
lsof -ti:8003 | xargs kill -9 2>/dev/null || true
lsof -ti:8080 | xargs kill -9 2>/dev/null || true

echo "✅ All DocSage services have been stopped."