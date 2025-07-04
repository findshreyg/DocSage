# Project API Documentation

## Overview
This document provides a comprehensive overview of the API endpoints available in the project, including authentication, file management, conversation handling, and question handling services.

## Authentication Service

### Overview
The Authentication Service handles user registration, login, authentication, and password management. It interfaces with AWS Cognito for user management and provides authentication tokens for secure access to other services.

### API Endpoints

#### 1. User Registration
- **Endpoint**: `/auth/signup`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword"
  }
  ```
- **Response**:
  - **Success**: 201 Created
  - **Error**: 400 Bad Request

#### 2. Confirm Registration
- **Endpoint**: `/auth/confirm`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "code": "123456"
  }
  ```
- **Response**:
  - **Success**: 200 OK
  - **Error**: 400 Bad Request

#### 3. Resend Confirmation Code
- **Endpoint**: `/auth/resend`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response**:
  - **Success**: 200 OK
  - **Error**: 400 Bad Request

#### 4. User Login
- **Endpoint**: `/auth/login`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securepassword"
  }
  ```
- **Response**:
  - **Success**: 200 OK
  - **Error**: 401 Unauthorized

#### 5. Refresh Token
- **Endpoint**: `/auth/refresh`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "refresh_token": "token"
  }
  ```
- **Response**:
  - **Success**: 200 OK
  - **Error**: 401 Unauthorized

#### 6. Forgot Password
- **Endpoint**: `/auth/forgot`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Response**:
  - **Success**: 200 OK
  - **Error**: 400 Bad Request

#### 7. Confirm Forgot Password
- **Endpoint**: `/auth/confirm-forgot`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "code": "123456",
    "new_password": "newsecurepassword"
  }
  ```
- **Response**:
  - **Success**: 200 OK
  - **Error**: 400 Bad Request

#### 8. Change Password
- **Endpoint**: `/auth/change-password`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "access_token": "token",
    "old_password": "oldpassword",
    "new_password": "newpassword"
  }
  ```
- **Response**:
  - **Success**: 200 OK
  - **Error**: 401 Unauthorized

#### 9. Get User Information
- **Endpoint**: `/auth/user`
- **Method**: GET
- **Headers**: 
  - `Authorization: Bearer <access_token>`
- **Response**:
  - **Success**: 200 OK
  - **Error**: 401 Unauthorized

#### 10. Delete User
- **Endpoint**: `/auth/delete`
- **Method**: DELETE
- **Headers**: 
  - `Authorization: Bearer <access_token>`
- **Response**:
  - **Success**: 200 OK
  - **Error**: 401 Unauthorized

#### 11. Logout
- **Endpoint**: `/auth/logout`
- **Method**: POST
- **Headers**: 
  - `Authorization: Bearer <access_token>`
- **Response**:
  - **Success**: 200 OK
  - **Error**: 401 Unauthorized

### Security
All endpoints require secure handling of authentication tokens. Ensure tokens are validated and expired tokens are rejected.

### Notes
- Ensure all sensitive data is encrypted and stored securely.
- Follow best practices for password management and token handling.

## File Management Service

### Overview
The File Management Service handles file uploads and downloads, managing user-uploaded content securely.

### API Endpoints

#### 1. Upload File
- **Endpoint**: `/upload`
- **Method**: POST
- **Request Body**: Multipart form data
- **Response**:
  - **Success**: 201 Created
  - **Error**: 400 Bad Request

#### 2. List Uploads
- **Endpoint**: `/upload/list`
- **Method**: GET
- **Headers**: 
  - `Authorization: Bearer <access_token>`
- **Response**:
  - **Success**: 200 OK
  - **Error**: 401 Unauthorized

#### 3. Delete File
- **Endpoint**: `/upload/delete`
- **Method**: DELETE
- **Request Body**:
  ```json
  {
    "file_id": "file123"
  }
  ```
- **Response**:
  - **Success**: 200 OK
  - **Error**: 400 Bad Request

## Conversation Management Service

### Overview
The Conversation Management Service handles user conversations, including retrieval, deletion, and search.

### API Endpoints

#### 1. Get Conversations
- **Endpoint**: `/conversation`
- **Method**: GET
- **Headers**: 
  - `Authorization: Bearer <access_token>`
- **Response**:
  - **Success**: 200 OK
  - **Error**: 401 Unauthorized

#### 2. Delete Conversation
- **Endpoint**: `/conversation/delete`
- **Method**: DELETE
- **Request Body**:
  ```json
  {
    "conversation_id": "conv123"
  }
  ```
- **Response**:
  - **Success**: 200 OK
  - **Error**: 400 Bad Request

#### 3. Find Conversation
- **Endpoint**: `/conversation/find`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "query": "search term"
  }
  ```
- **Response**:
  - **Success**: 200 OK
  - **Error**: 400 Bad Request

## Question Handling Service

### Overview
The Question Handling Service manages interactions related to asking and answering questions.

### API Endpoints

#### 1. Ask Question
- **Endpoint**: `/ask`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "question": "What is the capital of France?"
  }
  ```
- **Response**:
  - **Success**: 200 OK
  - **Error**: 400 Bad Request

## Security and Best Practices
- Ensure all services are secured using authentication tokens.
- Follow best practices for data encryption and secure storage.
- Regularly update and review security policies.
