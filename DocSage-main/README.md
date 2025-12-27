# 📄 DocSage - Intelligent Document Processing System

> Transform your documents into interactive knowledge with AI-powered analysis

DocSage is a modern, cloud-native document processing platform that lets you upload documents and ask intelligent questions about their content. Built with enterprise-grade security and scalability in mind.

## 🏗️ Project Structure

```
DocSage/
├── backend/                # Backend microservices
│   ├── auth_services/      # Authentication service (Port 8001)
│   ├── file_services/      # File processing service (Port 8002)
│   ├── conversation_services/ # Chat history service (Port 8003)
│   ├── llm_services/       # LLM Q&A service (Port 8004)
│   ├── docker-compose.yml  # Docker deployment
│   ├── start_services.sh   # Quick start script
│   └── README.md           # Backend documentation
├── docs/                   # API documentation
├── tests/                  # Test files
└── README.md              # This file
```

## ✨ What Can DocSage Do?

### 🤖 **Smart Document Analysis**

- Upload PDFs, Word docs, PowerPoints, and Excel files
- Ask natural language questions about your documents
- Get AI-powered answers with confidence scores and source citations
- Extract structured data from complex documents automatically

### 🔐 **Secure & Private**

- Personal user accounts with email verification
- Your documents are private and secure in AWS cloud storage
- Enterprise-grade authentication and data encryption
- Complete data deletion when you delete your account

### 💬 **Conversation History**

- Keep track of all your document conversations
- Search through previous questions and answers
- Organize conversations by document
- Export or delete conversation history anytime

### 🚀 **Fast & Reliable**

- Built on modern microservices architecture
- Automatic scaling based on usage
- 99.9% uptime with health monitoring
- Fast response times with intelligent caching

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd DocSage

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your AWS and Mistral AI credentials

# 3. Start all services
docker-compose up -d

# 4. Test the system
curl http://localhost:8001/auth/health
```

### Option 2: Manual Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env with your credentials

# 3. Start services individually
cd auth_services && uvicorn main:app --port 8001 &
cd file_services && uvicorn main:app --port 8002 &
cd conversation_services && uvicorn main:app --port 8003 &
cd llm_services && uvicorn main:app --port 8004 &
```

## 📋 Prerequisites

Before you start, you'll need:

### Required Accounts

- **AWS Account** - For secure cloud storage and user authentication
- **Mistral AI Account** - For AI-powered document analysis

### Required Software

- **Docker & Docker Compose** (recommended) OR **Python 3.8+**
- **Git** for cloning the repository

### AWS Resources (Auto-created with setup script)

- S3 bucket for document storage
- Cognito User Pool for authentication
- DynamoDB tables for metadata and conversations

## 🛠️ Technology Stack

- **🚀 Backend**: FastAPI (Python) - Fast, modern web framework
- **🔐 Authentication**: AWS Cognito - Enterprise-grade user management
- **☁️ Storage**: AWS S3 - Secure, scalable file storage
- **�️T Database**: AWS DynamoDB - NoSQL database for metadata
- **🤖 AI**: Mistral AI - Advanced language model for document analysis
- **🐳 Deployment**: Docker - Containerized microservices
- **Cloud Storage**: AWS S3 (boto3)
- **Database**: AWS DynamoDB for conversation and file metadata storage
- **AI/LLM**: Mistral LLM for document processing
- **Validation**: Pydantic
- **HTTP Client**: httpx, requests
- **Server**: uvicorn

## 🎯 How It Works

### 1. **Upload Your Documents**

- Drag and drop PDFs, Word docs, PowerPoints, or Excel files
- Files are securely stored in your private AWS S3 bucket
- Automatic document processing and metadata extraction

### 2. **Ask Questions**

- Type natural language questions about your documents
- "What is the total budget mentioned in this proposal?"
- "Who are the key stakeholders listed in this contract?"
- "What are the main risks identified in this report?"

### 3. **Get Intelligent Answers**

- AI analyzes your document and provides detailed answers
- Includes confidence scores and source citations
- Shows exactly where in the document the answer was found

### 4. **Manage Conversations**

- All your questions and answers are saved automatically
- Search through conversation history
- Organize by document or topic

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your credentials:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-docsage-bucket

# AWS Cognito (User Authentication)
COGNITO_USER_POOL_ID=your_user_pool_id
COGNITO_APP_CLIENT_ID=your_client_id
COGNITO_CLIENT_SECRET=your_client_secret

# DynamoDB Tables
DDB_TABLE=IDPMetadata
DYNAMODB_CONVERSATION_TABLE=IDPConversation

# Mistral AI
MISTRAL_API_KEY=your_mistral_api_key
MISTRAL_API_URL=https://api.mistral.ai/v1/chat/completions
MISTRAL_LLM_MODEL=mistral-large-latest
```

### Quick Setup Script

```bash
# Interactive setup (recommended)
./scripts/setup_env.sh interactive

# This will guide you through setting up all required credentials
```

### Environment Validation

Validate your environment configuration:

```bash
# Validate all settings including AWS resources
python scripts/validate_env.py

# Skip AWS validation (for testing)
python scripts/validate_env.py --skip-aws

# Validate specific env file
python scripts/validate_env.py --env-file custom.env
```

### Environment Management Commands

```bash
# Setup commands
./scripts/setup_env.sh interactive  # Interactive setup
./scripts/setup_env.sh template     # Create .env from template
./scripts/setup_env.sh copy         # Copy main .env to services
./scripts/setup_env.sh validate     # Validate configuration

# Validation commands
python scripts/validate_env.py      # Full validation
python scripts/validate_env.py --skip-aws  # Skip AWS checks
```

### Required Environment Variables

Each service has its own `.env.example` file, but the main configuration includes:

````env
# AWS Configuration (Required for all services)
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=us-east-1

# AWS S3 Configuration (File & LLM services)
S3_BUCKET_NAME=your-docsage-bucket

## 🎮 Using DocSage

### 1. **Start the System**
```bash
# Using Docker (recommended)
docker-compose up -d

# Check all services are running
curl http://localhost:8001/auth/health
curl http://localhost:8002/file/health
curl http://localhost:8003/conversation/health
curl http://localhost:8004/llm/health
````

### 2. **Create Your Account**

```bash
# Sign up for a new account
curl -X POST "http://localhost:8001/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "YourPassword123!",
    "name": "Your Name"
  }'

# Check your email and confirm your account
curl -X POST "http://localhost:8001/auth/confirm-signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "code": "123456"
  }'
```

### 3. **Login and Get Your Token**

```bash
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "YourPassword123!"
  }'

# Save the access_token from the response
```

### 4. **Upload a Document**

```bash
curl -X POST "http://localhost:8002/file/upload" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "file=@your-document.pdf"

# Save the file_hash from the response
```

### 5. **Ask Questions About Your Document**

```bash
curl -X POST "http://localhost:8004/llm/ask" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "file_hash": "YOUR_FILE_HASH",
    "question": "What is the main topic of this document?"
  }'
```

### 6. **View Your Conversations**

```bash
curl -X GET "http://localhost:8003/conversation/get-file-conversations?file_hash=YOUR_FILE_HASH" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🌐 Service Ports

When running locally, each service is available on:

- **🔐 Authentication**: `http://localhost:8001` - User accounts and login
- **📁 File Management**: `http://localhost:8002` - Upload and manage documents
- **💬 Conversations**: `http://localhost:8003` - Chat history and management
- **🤖 AI Processing**: `http://localhost:8004` - Ask questions about documents

## 📚 API Documentation

Interactive API documentation is available for each service:

- **Auth API**: `http://localhost:8001/docs`
- **File API**: `http://localhost:8002/docs`
- **Conversation API**: `http://localhost:8003/docs`
- **LLM API**: `http://localhost:8004/docs`

## 🧪 Testing Your Setup

### Quick Health Check

```bash
# Test all services are running
curl http://localhost:8001/auth/health
curl http://localhost:8002/file/health
curl http://localhost:8003/conversation/health
curl http://localhost:8004/llm/health
```

### Full API Test

```bash
# Run comprehensive API tests
python scripts/test_api.py --email your@email.com --password YourPassword123!
```

### Using Postman

1. Import `DocSage_Complete_Testing_Collection.json` into Postman
2. Follow the requests in order: Signup → Login → Upload → Ask Questions
3. See the [API Guide](docs/API_Guide.md) for detailed instructions

# Run all tests

pytest tests/

# Run with coverage

pytest --cov=. tests/

# Run specific service tests

pytest tests/auth_services/
pytest tests/file_services/

```

### Test Structure

```

tests/
├── conftest.py # Shared test configuration
├── test_main_orchestrator.py # Gateway/orchestrator tests
├── auth_services/ # Authentication service tests
│ ├── test_main.py
│ ├── test_authentication.py
│ ├── test_password_management.py
│ ├── test_user_management.py
│ └── test_utils.py
└── file_services/ # File service tests
└── test_file_service.py

````

### Test Features

- **Comprehensive Coverage**: Tests for all major endpoints and workflows
- **Mocked Dependencies**: AWS services and external APIs are mocked
- **Error Scenario Testing**: Both success and failure paths are tested
- **Integration Testing**: End-to-end workflow testing
- **Performance Testing**: Response time and load testing capabilities

## 📊 Monitoring & Observability

### Health Monitoring
- **Service Health Checks**: Individual health endpoints for each microservice
- **Centralized Health Dashboard**: `/health/services` endpoint shows all service statuses
- **Docker Health Checks**: Built-in container health monitoring
- **Automated Health Validation**: Deployment script includes health verification

### Logging
- **Structured Logging**: JSON-formatted logs with consistent fields
- **Log Levels**: Configurable logging levels (DEBUG, INFO, WARNING, ERROR)
- **Log Rotation**: Automatic log file rotation to prevent disk space issues
- **Centralized Configuration**: Shared logging configuration across all services

### Security
- **Input Validation**: Comprehensive request validation with Pydantic
- **Rate Limiting**: Built-in rate limiting to prevent abuse
- **Security Headers**: Standard security headers on all responses
- **File Upload Security**: File type and size validation
- **Token Validation**: JWT token format and expiration validation

### Performance
- **Response Time Logging**: Automatic performance metric collection
- **Connection Pooling**: Efficient HTTP client connection management
- **Async Processing**: Non-blocking request handling
- **Resource Optimization**: Minimal Docker images and efficient resource usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support, please contact the development team or create an issue in the repository.

## 🔄 Recent Improvements & Changelog

### Version 1.2.0 - Major Quality & Security Enhancements
- **🏗️ Complete API Gateway**: Implemented comprehensive orchestrator with request forwarding
- **🔒 Enhanced Security**: Added input validation, rate limiting, security headers, and file upload restrictions
- **📊 Improved Monitoring**: Structured logging, health checks, and performance monitoring
- **🧪 Comprehensive Testing**: Added API testing scripts and expanded unit test coverage
- **🐳 Production-Ready Deployment**: Docker Compose setup with health checks and automated deployment scripts
- **📝 Better Documentation**: Enhanced API documentation with response models and error handling
- **⚡ Performance Optimizations**: Async request handling, connection pooling, and resource optimization
- **🛡️ Error Handling**: Structured error responses and comprehensive exception handling
- **🔧 Configuration Management**: Environment template and validation
- **📈 Code Quality**: Type hints, docstrings, and consistent code patterns

## 🔧 Troubleshooting

### Common Issues

**Services won't start?**
```bash
# Check if ports are already in use
lsof -i :8001 -i :8002 -i :8003 -i :8004

# Check Docker containers
docker-compose ps
docker-compose logs
````

**Authentication errors?**

- Verify your AWS Cognito credentials in `.env`
- Check that your Cognito User Pool allows the configured authentication flows
- Ensure your AWS region is correct

**File upload fails?**

- Check your AWS S3 bucket permissions
- Verify your AWS credentials have S3 access
- Ensure the bucket exists in the correct region

**AI responses not working?**

- Verify your Mistral AI API key is valid
- Check your Mistral AI account has sufficient credits
- Ensure the model name is correct in your configuration

### Getting Help

1. **Check the logs**: `docker-compose logs [service-name]`
2. **Test individual services**: Use the health check endpoints
3. **Validate your setup**: Check all services respond with `{"health": "All Good"}`
4. **Review configuration**: Double-check your `.env` file

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. **Report Issues**: Found a bug? Open an issue with details
2. **Suggest Features**: Have an idea? We'd love to hear it
3. **Submit Code**: Fork the repo, make changes, submit a pull request
4. **Improve Documentation**: Help make our docs even better

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/your-username/docsage.git
cd docsage

# Create a development branch
git checkout -b feature/your-feature-name

# Make your changes and test them
docker-compose up -d && curl http://localhost:8001/auth/health

# Submit a pull request
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Mistral AI** for providing excellent language model capabilities
- **AWS** for reliable cloud infrastructure services
- **FastAPI** for the amazing web framework
- **Docker** for containerization technology

## 📞 Support

- **Documentation**: Check the `docs/` folder for detailed API documentation
- **Issues**: Report bugs or request features on GitHub
- **Community**: Join our discussions and share your use cases

---

**Built with passion for intelligent document processing**
