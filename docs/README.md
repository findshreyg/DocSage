# 📚 DocSage Documentation

Welcome to the DocSage documentation! Here you'll find everything you need to get started with intelligent document processing.

## 📖 Documentation Index

### 🚀 [Environment Setup Guide](Environment_Setup_Guide.md)

**Start here!** Complete guide to setting up DocSage in 15 minutes.

- Quick setup with Docker
- AWS and Mistral AI configuration
- Troubleshooting common issues
- Cost estimates and security tips

### 📚 [API Guide](API_Guide.md)

Complete reference for all DocSage API endpoints.

- Authentication endpoints
- File upload and management
- Document Q&A with AI
- Conversation management
- Example requests and responses

## 🎯 Quick Links

### For New Users

1. **[Setup Guide](Environment_Setup_Guide.md)** - Get DocSage running
2. **[API Guide](API_Guide.md)** - Learn the API endpoints
3. **Test with Postman** - Import `DocSage_Complete_Testing_Collection.json`

### For Developers

- **Interactive API Docs**: `http://localhost:PORT/docs` for each service
- **Health Checks**: `http://localhost:PORT/health` for monitoring
- **Source Code**: Well-commented Python code in each service directory

### For Troubleshooting

- **[Common Issues](Environment_Setup_Guide.md#-troubleshooting)** - Solutions to frequent problems
- **Service Logs**: `docker-compose logs [service-name]`
- **Health Status**: Check service endpoints at `/health`

## 🏗️ Architecture Overview

DocSage uses a microservices architecture with 4 independent services:

```
🔐 Authentication (Port 8001)  →  User accounts, login, security
📁 File Management (Port 8002)  →  Upload, store, manage documents
💬 Conversations (Port 8003)   →  Chat history, Q&A management
🤖 AI Processing (Port 8004)   →  Document analysis, question answering
```

Each service:

- Runs independently in its own container
- Has its own API documentation at `/docs`
- Includes comprehensive error handling
- Provides health monitoring at `/health`

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python) - Modern, fast web framework
- **AI**: Mistral AI - Advanced language models
- **Storage**: AWS S3 - Secure cloud file storage
- **Database**: AWS DynamoDB - NoSQL for metadata and conversations
- **Auth**: AWS Cognito - Enterprise user management
- **Deployment**: Docker - Containerized microservices

## 📝 Example Usage

```bash
# 1. Start DocSage
docker-compose up -d

# 2. Create account
curl -X POST "http://localhost:8001/auth/signup" \
  -d '{"email":"you@example.com","password":"Pass123!","name":"Your Name"}'

# 3. Upload document
curl -X POST "http://localhost:8002/file/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"

# 4. Ask questions
curl -X POST "http://localhost:8004/llm/ask" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"file_hash":"HASH","question":"What is this document about?"}'
```

## 🤝 Contributing

Found an issue or want to contribute?

- **Report bugs**: Create an issue with details
- **Suggest features**: We'd love to hear your ideas
- **Improve docs**: Help make our documentation even better
- **Submit code**: Fork, develop, test, and submit a pull request

## 📞 Support

- **Documentation Issues**: Check this docs folder
- **Setup Problems**: See the [troubleshooting section](Environment_Setup_Guide.md#-troubleshooting)
- **API Questions**: Refer to the [API Guide](API_Guide.md)
- **Feature Requests**: Open an issue on GitHub

---

**Ready to get started?** Begin with the [Environment Setup Guide](Environment_Setup_Guide.md)!
