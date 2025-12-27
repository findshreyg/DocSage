#!/bin/bash

# DocSage - Start All Services Script
# This script starts both frontend and backend services

echo "🚀 Starting DocSage Application..."

# Function to check if a port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null ; then
        echo "⚠️  Port $1 is already in use"
        return 1
    else
        return 0
    fi
}

# Function to start backend services
start_backend() {
    echo "📡 Starting Backend Services..."
    
    # Check if .env exists
    if [ ! -f "backend/.env" ]; then
        echo "⚠️  Backend .env file not found. Please copy backend/.env.example to backend/.env and configure it."
        return 1
    fi
    
    # Start backend services using docker-compose
    cd backend
    if [ -f "docker-compose.yml" ]; then
        echo "🐳 Starting services with Docker Compose..."
        docker-compose up -d
    else
        echo "📦 Starting services individually..."
        # Start each service in background
        cd auth_services && python -m uvicorn main:app --host 0.0.0.0 --port 8000 &
        cd ../file_services && python -m uvicorn main:app --host 0.0.0.0 --port 8002 &
        cd ../conversation_services && python -m uvicorn main:app --host 0.0.0.0 --port 8001 &
        cd ../llm_services && python -m uvicorn main:app --host 0.0.0.0 --port 8003 &
        cd ..
    fi
    
    # Start API Gateway
    echo "🌐 Starting API Gateway..."
    python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload &
    
    cd ..
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting Frontend..."
    
    # Check if node_modules exists
    if [ ! -d "frontend/node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        cd frontend && npm install && cd ..
    fi
    
    # Start frontend
    cd frontend
    npm run dev &
    cd ..
}

# Main execution
echo "🔍 Checking prerequisites..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js first."
    exit 1
fi

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python is not installed. Please install Python first."
    exit 1
fi

# Check ports
echo "🔍 Checking ports..."
check_port 3000 || echo "Frontend port 3000 is in use"
check_port 8080 || echo "API Gateway port 8080 is in use"

# Start services
start_backend
sleep 5  # Give backend time to start
start_frontend

echo ""
echo "✅ DocSage is starting up!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🌐 API Gateway: http://localhost:8080"
echo "📊 API Health: http://localhost:8080/health"
echo ""
echo "To stop all services, run: ./stop_all_services.sh"
echo "Or press Ctrl+C to stop this script and manually stop services"

# Wait for user input to keep script running
read -p "Press Enter to stop all services..."

# Stop services
echo "🛑 Stopping services..."
pkill -f "uvicorn"
pkill -f "npm run dev"
if [ -f "backend/docker-compose.yml" ]; then
    cd backend && docker-compose down && cd ..
fi

echo "✅ All services stopped."