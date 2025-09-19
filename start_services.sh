#!/bin/bash

echo "🚀 Starting DocSage Services..."
echo "================================"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Please create one based on .env.example"
    echo "📋 Required environment variables:"
    echo "   - AWS credentials and region"
    echo "   - Cognito configuration"
    echo "   - S3 bucket name"
    echo "   - DynamoDB table names"
    echo "   - Mistral API configuration"
    exit 1
fi

echo "🔧 Building and starting services..."
docker-compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "🔍 Testing service health..."

# Check each service health endpoint
services=(
    "Auth Service:http://localhost:8001/auth/health"
    "File Service:http://localhost:8002/file/health"
    "Conversation Service:http://localhost:8003/conversation/health"
    "LLM Service:http://localhost:8004/llm/health"
)

all_healthy=true

for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    url=$(echo $service | cut -d: -f2-)
    
    echo -n "Checking $name... "
    
    # Try up to 3 times with 2 second delays
    for i in {1..3}; do
        response=$(curl -s --max-time 5 "$url" 2>/dev/null)
        if [[ $? -eq 0 ]] && [[ $response == *"All Good"* ]]; then
            echo "✅ Healthy"
            break
        elif [[ $i -eq 3 ]]; then
            echo "❌ Not responding"
            all_healthy=false
        else
            sleep 2
        fi
    done
done

if $all_healthy; then
    echo ""
    echo "✅ All services are running successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Import DocSage_Complete_Testing_Collection.json into Postman"
    echo "2. Follow docs/API_Guide.md for detailed API documentation"
    echo "3. Services are available at:"
    echo "   - Auth Service: http://localhost:8001"
    echo "   - File Service: http://localhost:8002"
    echo "   - Conversation Service: http://localhost:8003"
    echo "   - LLM Service: http://localhost:8004"
    echo ""
    echo "📚 Interactive API docs available at each service's /docs endpoint"
    echo "🛑 To stop services: docker-compose down"
else
    echo ""
    echo "❌ Some services failed to start properly."
    echo "🔧 Troubleshooting:"
    echo "   - Check logs: docker-compose logs"
    echo "   - Verify .env configuration"
    echo "   - Ensure ports 8001-8004 are available"
    echo "🛑 Stop services: docker-compose down"
    exit 1
fi