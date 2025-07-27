# DocSage

A FastAPI-based intelligent document processing system that allows users to upload documents, ask questions about them, and receive AI-powered responses using LLM technology. Built with a modern microservices architecture for scalability, maintainability, and independent deployment.

## 🚀 Features

- **🔐 User Authentication**: Complete user lifecycle management with AWS Cognito integration
  - Secure registration and email confirmation
  - JWT-based authentication and authorization
  - Password management (reset, change, forgot password)
  - User profile management and account deletion
- **📄 Document Upload & Management**: Secure file handling with cloud storage
  - Multi-format support (PDF, DOCX, PPT, etc.)
  - AWS S3 integration for secure storage
  - File metadata tracking and organization
  - Presigned URLs for secure downloads
- **🤖 AI-Powered Document Processing**: Advanced LLM integration
  - Mistral AI for intelligent document analysis
  - Context-aware question answering
  - Confidence scoring and reasoning explanation
  - Source verification and citations
- **💬 Conversation Management**: Complete conversation lifecycle
  - Track conversations per document and user
  - Conversation history and retrieval
  - Bulk conversation management
- **🏗️ Microservices Architecture**: Independent, scalable services
  - Service isolation and independent deployment
  - Docker containerization for all services
  - Health monitoring for each service
- **🔒 Enterprise Security**: Comprehensive security measures
  - Bearer token authentication across all services
  - User-specific data isolation
  - Secure file access controls
  - Input validation and sanitization
- **📊 Testing & Quality Assurance**: Comprehensive test coverage
  - Unit tests for all authentication services
  - Integration testing capabilities
  - Mocked external dependencies

## 🏗️ Architecture

The project follows a **microservices architecture** with independent services that can be deployed, scaled, and maintained separately:

```
├── 🔐 auth_services/             # Authentication & User Management Service (Port 8000)
│   ├── main.py                   # FastAPI application
│   ├── authentication.py         # Login, logout, token management
│   ├── password_management.py     # Password operations
│   ├── user_management.py        # User lifecycle management
│   ├── utils.py                  # Helper functions
│   ├── schemas.py               # Pydantic models
│   ├── requirements.txt         # Service dependencies
│   ├── Dockerfile              # Container configuration
│   └── .dockerignore           # Docker build optimization
├── 💬 conversation_services/     # Conversation Management Service (Port 8001)
│   ├── main.py                  # FastAPI application
│   ├── conversation_handler.py  # Conversation CRUD operations
│   ├── utils.py                 # Authentication utilities
│   ├── schemas.py              # Request/response models
│   ├── requirements.txt        # Service dependencies
│   ├── Dockerfile             # Container configuration
│   └── .dockerignore          # Docker build optimization
├── 📁 file_services/            # File Management Service (Port 8002)
│   ├── main.py                 # FastAPI application
│   ├── file_handler.py         # File operations (upload, download, delete)
│   ├── utils.py                # Authentication utilities
│   ├── schemas.py             # Request/response models
│   ├── requirements.txt       # Service dependencies
│   ├── Dockerfile            # Container configuration
│   └── .dockerignore         # Docker build optimization
├── 🤖 llm_services/             # LLM Processing Service (Port 8003)
│   ├── main.py                 # FastAPI application
│   ├── mistral_llm.py          # Mistral AI integration
│   ├── utils.py                # Authentication utilities
│   ├── schemas.py             # Request/response models
│   ├── requirements.txt       # Service dependencies
│   ├── Dockerfile            # Container configuration
│   └── .dockerignore         # Docker build optimization
├── 🧪 tests/                   # Comprehensive Test Suite
│   ├── __init__.py
│   └── auth_services/          # Authentication service tests
│       ├── __init__.py
│       ├── test_main.py        # API endpoint tests
│       ├── test_authentication.py  # Auth logic tests
│       ├── test_password_management.py  # Password tests
│       ├── test_user_management.py  # User management tests
│       └── test_utils.py       # Utility function tests
├── 📚 docs/                    # Comprehensive API Documentation
│   ├── Auth API Document.md    # Authentication service docs
│   ├── File Service API Documentation.md  # File service docs
│   ├── LLM Service API Document.md  # LLM service docs
│   └── Convo API Documentation.md  # Conversation service docs
├── main.py                     # Main application orchestrator
└── README.md                   # This file
```

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Authentication**: JWT tokens, AWS Cognito
- **Cloud Storage**: AWS S3 (boto3)
- **Database**: AWS DynamoDB for conversation and file metadata storage
- **AI/LLM**: Mistral LLM for document processing
- **Validation**: Pydantic
- **HTTP Client**: httpx, requests
- **Server**: uvicorn

## 📋 Prerequisites

- Python 3.8+
- AWS Account (for S3 storage and Cognito authentication)
- Mistral AI API access

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd "Intelligent Document Processing"
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the root directory with the following variables:
   ```env
   # AWS Configuration
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=your_region
   S3_BUCKET_NAME=your_bucket_name
   
   # AWS Cognito Configuration
   COGNITO_USER_POOL_ID=your_user_pool_id
   COGNITO_CLIENT_ID=your_client_id
   COGNITO_CLIENT_SECRET=your_client_secret
   
   # Mistral AI Configuration
   MISTRAL_API_KEY=your_mistral_api_key
   
   # JWT Configuration
   JWT_SECRET_KEY=your_jwt_secret
   JWT_ALGORITHM=HS256
   ```

## 🚀 Deployment & Usage

### Option 1: Microservices Deployment (Recommended)

Each service can be deployed independently using Docker:

#### Authentication Service (Port 8000)
```bash
cd auth_services
docker build -t auth-service .
docker run -p 8000:8000 --env-file ../.env auth-service
```

#### Conversation Service (Port 8001)
```bash
cd conversation_services
docker build -t conversation-service .
docker run -p 8001:8001 --env-file ../.env conversation-service
```

#### File Service (Port 8002)
```bash
cd file_services
docker build -t file-service .
docker run -p 8002:8002 --env-file ../.env file-service
```

#### LLM Service (Port 8003)
```bash
cd llm_services
docker build -t llm-service .
docker run -p 8003:8003 --env-file ../.env llm-service
```

### Option 2: Development Mode (Main Orchestrator)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Service Health Checks

Each service has its own health check endpoint:
- **Auth Service**: `http://localhost:8000/auth/health`
- **Conversation Service**: `http://localhost:8001/conversation/health`
- **File Service**: `http://localhost:8002/file/health`
- **LLM Service**: `http://localhost:8003/llm/health`

### API Documentation

Each service provides its own interactive documentation:
- **Auth Service**: `http://localhost:8000/docs`
- **Conversation Service**: `http://localhost:8001/docs`
- **File Service**: `http://localhost:8002/docs`
- **LLM Service**: `http://localhost:8003/docs`

### Service Dependencies

Each service has its own `requirements.txt` with optimized dependencies:
- **Auth Service**: FastAPI, boto3, pydantic, uvicorn
- **Conversation Service**: FastAPI, boto3, pydantic, uvicorn
- **File Service**: FastAPI, boto3, python-multipart, uvicorn
- **LLM Service**: FastAPI, mistralai, scikit-learn, uvicorn

## 🔗 API Endpoints

### Authentication (`/auth`)
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `POST /auth/confirm-signup` - Confirm user registration
- `POST /auth/resend-confirmation-code` - Resend confirmation code
- `POST /auth/refresh-token` - Refresh JWT token
- `POST /auth/forgot-password` - Initiate password reset
- `POST /auth/confirm-forgot-password` - Confirm password reset
- `POST /auth/change-password` - Change user password
- `GET /auth/get-user` - Get user details
- `DELETE /auth/delete-user` - Delete user account

### File Upload (`/upload`)
- `POST /upload/` - Upload a document
- `GET /upload/list-uploads` - List user's uploaded files
- `DELETE /upload/delete-file` - Delete a specific file

### File Download (`/download`)
- `POST /download/file` - Generate presigned URL for file download

### Document Q&A (`/ask`)
- `POST /ask/` - Ask questions about uploaded documents

### Conversation Management (`/conversation`)
- `POST /conversation/get-all-conversations` - Get all conversations
- `POST /conversation/find-conversation` - Find specific conversation
- `DELETE /conversation/delete-conversation` - Delete specific conversation
- `DELETE /conversation/delete-all-conversations` - Delete all conversations for a file

### Health Check
- `GET /` - Health check endpoint

## 📝 Request/Response Examples

### Upload Document
```bash
curl -X POST "http://localhost:8000/upload/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@document.pdf"
```

### Ask Question
```bash
curl -X POST "http://localhost:8000/ask/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the main topic of this document?",
    "file_hash": "abc123def456"
  }'
```

## 🔐 Security Features

- **JWT Authentication**: Secure token-based authentication
- **User-specific File Access**: Users can only access their own files
- **Secure File Storage**: Files stored in AWS S3 with proper access controls
- **Input Validation**: All inputs validated using Pydantic schemas
- **Error Handling**: Comprehensive error handling and logging
- **Monitoring**: Health check endpoint for monitoring application status

## 🧪 Testing

The project includes a comprehensive test suite focusing on the authentication service:

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest tests/

# Run specific test file
pytest tests/auth_services/test_main.py

# Run with coverage
pytest --cov=auth_services tests/auth_services/
```

### Test Structure

- **`tests/auth_services/test_main.py`**: API endpoint testing
- **`tests/auth_services/test_authentication.py`**: Authentication logic tests
- **`tests/auth_services/test_password_management.py`**: Password management tests
- **`tests/auth_services/test_user_management.py`**: User management tests
- **`tests/auth_services/test_utils.py`**: Utility function tests

### Test Features

- **Mocked External Dependencies**: AWS Cognito calls are mocked for isolated testing
- **FastAPI TestClient**: Comprehensive API endpoint testing
- **Dependency Override**: Authentication dependencies can be overridden for testing
- **Error Scenario Testing**: Tests cover both success and failure scenarios

## 📊 Monitoring

The application includes:
- **Service Health Checks**: Individual health endpoints for each microservice
- **Comprehensive Error Handling**: Structured error responses with proper HTTP status codes
- **Structured Logging**: Detailed logging for debugging and monitoring
- **Service Isolation**: Independent service monitoring and alerting capabilities

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

## 🔄 Changelog

### Version 1.1.0
- Refactored to microservices architecture
- Separated services: auth, file, conversation, LLM
- Dockerized each service
- Updated API documentation

### Version 1.0.0
- Initial release
- User authentication system
- Document upload and storage
- AI-powered document Q&A
- Conversation management
- File management features
