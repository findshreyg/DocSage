# 📚 DocSage API Guide

> Complete reference for all DocSage API endpoints

## 🌐 Base URLs

When running locally:
- **Authentication Service**: `http://localhost:8001`
- **File Service**: `http://localhost:8002`
- **Conversation Service**: `http://localhost:8003`
- **LLM Service**: `http://localhost:8004`

## 🔐 Authentication

All API endpoints (except health checks) require a Bearer token in the Authorization header:

```bash
Authorization: Bearer YOUR_ACCESS_TOKEN
```

Get your access token by logging in through the Authentication Service.

---

## 🔑 Authentication Service (Port 8001)

### Health Check
```http
GET /auth/health
```
**Response**: `{ "health": "All Good" }`

### Sign Up
```http
POST /auth/signup
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "YourPassword123!",
  "name": "Your Full Name"
}
```
**Response**: `{ "message": "User account created for user@example.com." }`

### Confirm Sign Up
```http
POST /auth/confirm-signup
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}
```
**Response**: `{ "message": "User confirmed successfully." }`

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "YourPassword123!"
}
```
**Response**:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "id_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "name": "Your Full Name",
  "email": "user@example.com"
}
```

### Get User Info
```http
GET /auth/get-user
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**Response**:
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "name": "Your Full Name"
}
```

### Change Password
```http
POST /auth/change-password
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword456!"
}
```

### Forgot Password
```http
POST /auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

### Delete Account
```http
DELETE /auth/delete-user
Authorization: Bearer YOUR_ACCESS_TOKEN
```

---

## 📁 File Service (Port 8002)

### Health Check
```http
GET /file/health
```

### Upload File
```http
POST /file/upload
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data

file: [your-document.pdf]
```
**Response**:
```json
{
  "message": "Upload successful with adaptive extraction",
  "s3_key": "user-id/filename.pdf",
  "file_hash": "abc123def456...",
  "document_type": "property schedule of values",
  "classification_confidence": 0.9,
  "extracted_fields_count": 5
}
```

### List Files
```http
GET /file/list-uploads
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**Response**:
```json
{
  "files": [
    {
      "filename": "document.pdf",
      "hash": "abc123def456",
      "upload_date": "2024-01-15T10:30:00Z",
      "file_size": 1024000
    }
  ]
}
```

### Delete File
```http
DELETE /file/delete-file
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "file_hash": "abc123def456"
}
```

### Generate Download Link
```http
POST /file/download
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "file_hash": "abc123def456"
}
```
**Response**:
```json
{
  "url": "https://your-bucket.s3.amazonaws.com/presigned-url"
}
```

---

## 💬 Conversation Service (Port 8003)

### Health Check
```http
GET /conversation/health
```

### Get File Conversations
```http
GET /conversation/get-file-conversations?file_hash=abc123def456
Authorization: Bearer YOUR_ACCESS_TOKEN
```
**Response**:
```json
{
  "conversations": [
    {
      "question": "What is the main topic?",
      "answer": "This document discusses...",
      "confidence": 0.95,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "message": "Conversations retrieved successfully."
}
```

### Find Specific Conversation
```http
POST /conversation/find-conversation
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "file_hash": "abc123def456",
  "question": "What is the policy number?"
}
```

### Delete Conversation
```http
DELETE /conversation/delete-conversation
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "file_hash": "abc123def456",
  "question": "What is the policy number?"
}
```

### Delete All Conversations for File
```http
DELETE /conversation/delete-all-conversations
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "file_hash": "abc123def456"
}
```

---

## 🤖 LLM Service (Port 8004)

### Health Check
```http
GET /llm/health
```

### Ask Question
```http
POST /llm/ask
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "file_hash": "abc123def456",
  "question": "What is the total budget mentioned in this document?"
}
```
**Response**:
```json
{
  "question": "What is the total budget mentioned in this document?",
  "answer": "The total budget mentioned is $2.5 million for the fiscal year 2024.",
  "confidence": 0.92,
  "reasoning": "Found in section 3.2 of the financial summary table.",
  "source": {
    "location": "Page 5, Section 3.2",
    "search_anchor": "Total Budget: $2.5M",
    "page_number": 5,
    "extraction_method": "explicit"
  },
  "verified": true,
  "total_pages": 12
}
```

### Extract Adaptive Data
```http
POST /llm/extract-adaptive
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
  "file_hash": "abc123def456"
}
```
**Response**:
```json
{
  "file_hash": "abc123def456",
  "adaptive_extraction": {
    "classification": {
      "document_type": "property schedule of values",
      "description": "A document listing properties with insurance details",
      "confidence": 0.9
    },
    "field_values": {
      "properties": {
        "confidence": 0.9,
        "value": "{'location': 'London', 'value': '$11,865,900', ...}"
      },
      "report_date": {
        "confidence": 0.85,
        "value": "5/15/2021-22"
      }
    },
    "extraction_status": "success",
    "extraction_timestamp": "2024-01-15T10:30:00Z"
  }
}
```

---

## 🚨 Error Responses

All services return consistent error responses:

```json
{
  "error": true,
  "message": "Detailed error message",
  "status_code": 400
}
```

### Common Status Codes
- **200**: Success
- **201**: Created (for signup, upload)
- **400**: Bad Request (invalid input)
- **401**: Unauthorized (missing/invalid token)
- **404**: Not Found (resource doesn't exist)
- **409**: Conflict (user already exists)
- **422**: Validation Error (invalid data format)
- **500**: Internal Server Error

---

## 📝 Example Workflows

### Complete User Journey
```bash
# 1. Sign up
curl -X POST "http://localhost:8001/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","name":"Test User"}'

# 2. Confirm signup (check email for code)
curl -X POST "http://localhost:8001/auth/confirm-signup" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","code":"123456"}'

# 3. Login
curl -X POST "http://localhost:8001/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'

# 4. Upload document
curl -X POST "http://localhost:8002/file/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf"

# 5. Ask question
curl -X POST "http://localhost:8004/llm/ask" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"file_hash":"YOUR_FILE_HASH","question":"What is this document about?"}'

# 6. View conversations
curl -X GET "http://localhost:8003/conversation/get-file-conversations?file_hash=YOUR_FILE_HASH" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Document Processing Workflow
```bash
# Upload → Extract → Ask → Manage
curl -X POST "http://localhost:8002/file/upload" -H "Authorization: Bearer TOKEN" -F "file=@doc.pdf"
curl -X POST "http://localhost:8004/llm/extract-adaptive" -H "Authorization: Bearer TOKEN" -d '{"file_hash":"HASH"}'
curl -X POST "http://localhost:8004/llm/ask" -H "Authorization: Bearer TOKEN" -d '{"file_hash":"HASH","question":"Summary?"}'
curl -X GET "http://localhost:8003/conversation/get-file-conversations?file_hash=HASH" -H "Authorization: Bearer TOKEN"
```

---

## 🔧 Testing Tools

### Postman Collection
Import `DocSage_Complete_Testing_Collection.json` for pre-configured requests.

### Health Check Commands
```bash
# Check all services
curl http://localhost:8001/auth/health
curl http://localhost:8002/file/health
curl http://localhost:8003/conversation/health
curl http://localhost:8004/llm/health
```

### Full API Test
```bash
python scripts/test_api.py --email your@email.com --password YourPassword123!
```

---

**💡 Tip**: Use the interactive API documentation at `http://localhost:PORT/docs` for each service to test endpoints directly in your browser.