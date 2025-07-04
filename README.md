# DocSage

A FastAPI-based intelligent document processing system that allows users to upload documents, ask questions about them, and receive AI-powered responses using LLM technology.

## 🚀 Features

- **User Authentication**: Secure user registration, login, and session management
- **Document Upload**: Upload and securely store documents in cloud storage
- **Document Processing**: AI-powered document analysis and question answering
- **Conversation Management**: Track and manage conversations about specific documents
- **File Management**: List, download, and delete uploaded files
- **Secure API**: JWT-based authentication with protected endpoints

## 🏗️ Architecture

The project follows a modular architecture with the following components:

```
├── api/                    # API route handlers
│   ├── routes_auth.py      # Authentication endpoints
│   ├── routes_upload.py    # File upload endpoints
│   ├── routes_download.py  # File download endpoints
│   ├── routes_conversation.py # Conversation management
│   └── routes_ask.py       # AI question answering
├── auth_services/          # Authentication services
├── models/                 # Pydantic schemas and data models
├── services/               # Business logic services
├── upload/                 # File upload handlers
├── download/               # File download handlers
├── conversation/           # Conversation management
└── main.py                 # FastAPI application entry point
```

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Authentication**: JWT tokens, AWS Cognito
- **Cloud Storage**: AWS S3 (boto3)
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

## 🚀 Usage

### Starting the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### API Documentation

Once the server is running, you can access:
- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc documentation**: `http://localhost:8000/redoc`

## 🔗 API Endpoints

### Authentication (`/auth`)
- `POST /auth/signup` - User registration
- `POST /auth/login` - User login
- `POST /auth/confirm` - Confirm user registration
- `POST /auth/resend` - Resend confirmation code
- `POST /auth/refresh` - Refresh JWT token
- `POST /auth/forgot-password` - Initiate password reset
- `POST /auth/confirm-forgot-password` - Confirm password reset
- `POST /auth/change-password` - Change user password

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

## 🧪 Testing

To run tests (if available):
```bash
pytest
```

## 📊 Monitoring

The application includes:
- Health check endpoint for monitoring
- Comprehensive error handling
- Structured logging

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

### Version 1.0.0
- Initial release
- User authentication system
- Document upload and storage
- AI-powered document Q&A
- Conversation management
- File management features
