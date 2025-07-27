

# 🗨️ Conversation API Documentation

## Overview

This document describes the **Conversation Services API** for the Intelligent Document Processing system.  
It provides endpoints to **find**, **get**, **delete**, and **manage** user conversations for processed files and questions.

---

## ✅ Base URL

```
http://localhost:8001
```

---

## 📂 Endpoints

### 🔹 Health Check

- **Endpoint**: `/conversation/health`
- **Method**: GET
- **Description**: Check that the conversation service is running.
- **Response**:
  - `200 OK`: `{ "health": "All Good" }`

---

### 🔹 Get All Conversations for a user under a file

- **Endpoint**: `/conversation/get-file-conversations`
- **Method**: POST
- **Description**: Retrieve **all conversations** for the authenticated user.
- **Headers**:
  - `Authorization`: Bearer token
- **Request Body**:
  ```json
  {
    "file_hash": "file123hash"
  }
  ```
- **Responses**:
  - `200 OK`: `{ "conversations": [...], "message": "Conversations retrieved successfully." }`
  - `401 Unauthorized`: Authorization header missing.
  - `500 Internal Server Error`: Unexpected error.

---

### 🔹 Find Conversation

- **Endpoint**: `/conversation/find-conversation`
- **Method**: POST
- **Description**: Find a specific conversation for a **file hash** and **question**.
- **Headers**:
  - `Authorization`: Bearer token
- **Request Body**:
  ```json
  {
    "file_hash": "file123hash",
    "question": "What is the policy number?"
  }
  ```
- **Responses**:
  - `200 OK`: `{ "conversation_services": {...}, "message": "Conversation found successfully." }`
  - `401 Unauthorized`: Authorization header missing.
  - `404 Not Found`: Conversation not found.
  - `500 Internal Server Error`: Unexpected error.

---

### 🔹 Delete Conversation

- **Endpoint**: `/conversation/delete-conversation`
- **Method**: DELETE
- **Description**: Delete a specific conversation for a **file hash** and **question**.
- **Headers**:
  - `Authorization`: Bearer token
- **Request Body**:
  ```json
  {
    "file_hash": "file123hash",
    "question": "What is the policy number?"
  }
  ```
- **Responses**:
  - `200 OK`: `{ "message": "Conversation deleted successfully." }`
  - `401 Unauthorized`: Authorization header missing.
  - `404 Not Found`: Conversation not found.
  - `500 Internal Server Error`: Unexpected error.

---

### 🔹 Delete All Conversations

- **Endpoint**: `/conversation/delete-all-conversations`
- **Method**: DELETE
- **Description**: Delete **all conversations** for a specific **file hash** for the authenticated user.
- **Headers**:
  - `Authorization`: Bearer token
- **Request Body**:
  ```json
  {
    "file_hash": "file123hash"
  }
  ```
- **Responses**:
  - `200 OK`: `{ "message": "All conversations deleted successfully." }`
  - `401 Unauthorized`: Authorization header missing.
  - `404 Not Found`: No conversations found.
  - `500 Internal Server Error`: Unexpected error.

---

## ⚙️ Auth

All endpoints except `health` require a valid **Bearer token** in the `Authorization` header.

---

## ⚙️ Error Codes

- `4XX`: Client errors — invalid auth, not found.
- `5XX`: Unexpected server errors.

---

## 🐳 Deployment

Build and run using Docker:

```bash
docker build -t conversation-service . && docker run -p 8001:8001 conversation-service
```