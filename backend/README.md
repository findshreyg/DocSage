# DocSage Backend

This directory contains all the backend microservices and related files for the DocSage application.

## 🏗️ Architecture

DocSage backend consists of 4 microservices:

- **Auth Service** (`auth_services/`) - Port 8001: User authentication & management
- **File Service** (`file_services/`) - Port 8002: File upload, conversion & metadata extraction  
- **Conversation Service** (`conversation_services/`) - Port 8003: Chat history management
- **LLM Service** (`llm_services/`) - Port 8004: Document Q&A processing

## 🚀 Quick Start

1. **Setup Environment**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your actual credentials
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start All Services**:
   ```bash
   ./start_services.sh
   ```

4. **Test with Postman**:
   - Import `DocSage_Complete_Testing_Collection.json`
   - All services will be running on ports 8001-8004

## 📁 Directory Structure

```
backend/
├── auth_services/          # Authentication microservice
├── conversation_services/  # Chat history microservice  
├── file_services/         # File processing microservice
├── llm_services/          # LLM Q&A microservice
├── docker-compose.yml     # Docker deployment
├── start_services.sh      # Start all services script
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
└── DocSage_Complete_Testing_Collection.json  # Postman tests
```

## 🔧 Configuration

- **Environment Variables**: Copy `.env.example` to `.env` and configure
- **AWS Services**: S3, DynamoDB, Cognito required
- **Mistral AI**: API key required for LLM processing
- **LibreOffice**: Required for document conversion

## 📖 Documentation

See the `../docs/` directory for detailed API documentation and setup guides.