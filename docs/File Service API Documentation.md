# 📁 File Service API Documentation

## Overview

This document describes the **File Service API** for the Intelligent Document Processing system.  
It provides endpoints for securely uploading, listing, deleting, and downloading files using presigned URLs.

---

## ✅ Base URL

```
http://localhost:8002
```

---

## 📂 Endpoints

### 🔹 Health Check - TESTED OK

- **Endpoint**: `/file/health`
- **Method**: GET
- **Description**: Check if the File Service is running.
- **Response**:
  - `200 OK`: `{ "health": "All Good" }`

---

### 🔹 Upload File - TESTED OK

- **Endpoint**: `/file/upload`
- **Method**: POST
- **Description**: Upload a file (PDF, DOCX, PPT, etc.) to the user’s storage bucket.
- **Headers**:
  - `Authorization`: Bearer token (required)
- **Request**:
  - `multipart/form-data`: Contains the file.
- **Responses**:
  - `201 Created`: `{ "message": "File uploaded successfully", "file_path": "user/uploads/filename.pdf" }`
  - `400 Bad Request`: File missing or invalid.
  - `401 Unauthorized`: Authorization header missing or invalid.
  - `500 Internal Server Error`: Upload failed.

---

### 🔹 List Uploaded Files - TESTED OK

- **Endpoint**: `/file/list-uploads`
- **Method**: GET
- **Description**: List all files uploaded by the authenticated user.
- **Headers**:
  - `Authorization`: Bearer token (required)
- **Responses**:
  - `200 OK`: `{ "files": [ "file1.pdf", "file2.docx" ] }` or `{ "message": "No uploads found." }`
  - `401 Unauthorized`: Authorization header missing or invalid.
  - `500 Internal Server Error`: Failed to fetch files.

---

### 🔹 Delete File - TESTED OK

- **Endpoint**: `/file/delete-file`
- **Method**: DELETE
- **Description**: Delete a specific uploaded file using its `file_hash`.
- **Headers**:
  - `Authorization`: Bearer token (required)
- **Request Body**:
  ```json
  {
    "file_hash": "abc123filehash"
  }
  ```
- **Responses**:
  - `200 OK`: `{ "message": "File deleted successfully." }`
  - `400 Bad Request`: `file_hash` missing.
  - `401 Unauthorized`: Authorization header missing or invalid.
  - `404 Not Found`: File not found.
  - `500 Internal Server Error`: Deletion failed.

---

### 🔹 Generate Download Link - TESTED OK

- **Endpoint**: `/file/download`
- **Method**: POST
- **Description**: Generate a presigned URL to securely download a file.
- **Headers**:
  - `Authorization`: Bearer token (required)
- **Request Body**:
  ```json
  {
    "file_hash": "abc123filehash"
  }
  ```
- **Responses**:
  - `200 OK`: `{ "url": "https://presigned-s3-url" }`
  - `400 Bad Request`: `file_hash` missing.
  - `401 Unauthorized`: Authorization header missing or invalid.
  - `500 Internal Server Error`: Failed to generate download link.

---

## ⚙️ Auth

All endpoints except `health` require a valid **Bearer token** in the `Authorization` header.

---

## ⚙️ Schemas

Validated request models are defined in `schemas.py`:
- `DeleteFileRequest`
- `DownloadFileRequest`

---

## ⚙️ Dependencies

Defined in `requirements.txt`:
- `fastapi`
- `uvicorn`
- `boto3`
- `pydantic`
- `httpx`
- `python-dotenv`
- `python-multipart`

---

## 🐳 Deployment

Build and run the File Service using Docker:

```bash
docker build -t file-service . && docker run -p 8002:8002 file-service
```

---

✅ **File Service is ready for secure file upload, listing, deletion, and presigned URL downloads.**
