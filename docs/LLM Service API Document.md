# 🤖 LLM Service API Documentation

## Overview

This document describes the **LLM Service API** for the Intelligent Document Processing system.  
It defines endpoints for sending file-based questions to the Mistral LLM and receiving structured answers.

---

## ✅ Base URL

```
http://localhost:8003
```

---

## 📂 Endpoints

### 🔹 Health Check

- **Endpoint**: `/llm/health`
- **Method**: GET
- **Description**: Check that the LLM microservice is running.
- **Response**:
  - `200 OK`: `{ "health": "All Good" }`

---

### 🔹 Ask Question

- **Endpoint**: `/llm/ask`
- **Method**: POST
- **Description**: Submit a question with a `file_hash` to the Mistral LLM.
- **Headers**:
  - `Authorization`: Bearer token (required)
- **Request Body**:
  ```json
  {
    "file_hash": "abc123filehash",
    "question": "What is the policy coverage?"
  }
  ```
- **Responses**:
  - `200 OK`:
    ```json
    {
      "question": "What is the policy coverage?",
      "answer": "The policy covers up to $100,000 for liability.",
      "confidence": 0.95,
      "reasoning": "Extracted from section 3.1 of the document.",
      "source": "Internal file reference",
      "verified": true
    }
    ```
  - `401 Unauthorized`: Authorization header missing or invalid.
  - `400 Bad Request`: `file_hash` is required but missing.
  - `500 Internal Server Error`: Internal error or empty LLM response.

---

## ⚙️ Auth

The `/llm/ask` endpoint requires a valid **Bearer token** in the `Authorization` header.

---

## ⚙️ Required Field

- **`file_hash`**: Required. Identifies the uploaded document or file.
- **`question`**: Required. The user’s question for the LLM.

---

## ⚙️ Schemas

Validated request and response payloads are defined in `schemas.py`:
- `AskRequest`
- `AskResponse`

---

## 🐳 Deployment

Build and run the LLM Service with Docker:

```bash
docker build -t llm-service . && docker run -p 8003:8003 llm-service
```

---

**✅ LLM Service is ready to process file-based questions securely and return answers.**