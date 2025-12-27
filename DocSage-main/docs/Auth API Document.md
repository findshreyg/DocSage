

# 📑 Auth API Documentation

## Overview

This document describes the **Authentication & User Management API** for the Intelligent Document Processing system.  
It covers available endpoints under `/auth/`, request/response payloads, headers, and standard error cases.

---

## ✅ Base URL

```
http://localhost:8000
```

---

## 📂 Endpoints

### 🔹 Health Check - TESTED OK

- **Endpoint**: `/auth/health`
- **Method**: GET
- **Description**: Check that the authentication service is up.
- **Response**:
  - `200 OK`: `{ "health": "All Good" }`

---

### 🔹 Sign Up - TESTED OK

- **Endpoint**: `/auth/signup`
- **Method**: POST
- **Description**: Register a new user.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "YourPassword123!",
    "name": "Full Name"
  }
  ```
- **Response Body**:
   ```json
    {
    "message": "User account created for user@example.com"
    }
    ```   
- **Responses**:
  - `201 Created`: Account created. 
  - `400 Bad Request`: Invalid input.
  - `409 Conflict`: User already exists.

---

### 🔹 Login - TESTED OK

- **Endpoint**: `/auth/login`
- **Method**: POST
- **Description**: Authenticate a user.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "YourPassword123!"
  }
  ```
- **Responses**:
  - `200 OK`: `{ "access_token" : "hjsagdjahsgd...", "id_token" : "jsakhdashdakjs...", "refresh_token" : "jksahDKS..."" , "name" : "Full Name" : "email" : "user@example.com""}`
  - `401 Unauthorized`: Invalid credentials.

---

### 🔹 Refresh Token - TESTED OK but not used in current version

- **Endpoint**: `/auth/refresh-token`
- **Method**: POST
- **Description**: Refresh tokens with a valid refresh token.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "refresh_token": "VALID_REFRESH_TOKEN"
  }
  ```
- **Responses**:
  - `200 OK`: New tokens.
  - `401 Unauthorized`: Invalid or expired token.

---

### 🔹 Logout - TESTED OK

- **Endpoint**: `/auth/logout`
- **Method**: POST
- **Description**: Log out a user by invalidating the token.
- **Headers**:
  - `Authorization`: Bearer token (passed automatically with Depends)
- **Responses**:
  - `200 OK`: Logout successful.
  - `401 Unauthorized`: Invalid token.

---

### 🔹 Confirm Sign Up - TESTED OK

- **Endpoint**: `/auth/confirm-signup`
- **Method**: POST
- **Description**: Confirm sign up with a verification code.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "code": "123456"
  }
  ```
- **Responses**:
  - `200 OK`: Confirmed.```json {
    "message": "User confirmed successfully." }```
  
  - `400 Bad Request`: Invalid code or user.

---

### 🔹 Resend Confirmation Code - TESTED OK

- **Endpoint**: `/auth/resend-confirmation-code`
- **Method**: POST
- **Description**: Resend the email confirmation code.
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Responses**:
  - `200 OK`: Code resent.
  - `400 Bad Request`: Could not resend. or `400 Bad Request`: ```json {
    "detail": "User is already confirmed."
}``` if User already confirmed.

---

### 🔹 Forgot Password - TESTED OK

- **Endpoint**: `/auth/forgot-password`
- **Method**: POST
- **Description**: Start password reset flow.
- **Request Body**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **Responses**:
  - `200 OK`: ```json {
    "message": "Forgot password code sent successfully."
} ```
  - `400 Bad Request`: Failed to send.

---

### 🔹 Confirm Forgot Password - TESTED OK

- **Endpoint**: `/auth/confirm-forgot-password`
- **Method**: POST
- **Description**: Confirm reset with code and set new password.
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "confirmation_code": "123456",
    "new_password": "NewPassword123!"
  }
  ```
- **Responses**:
  - `200 OK`: ```json {
    "message": "Password reset successful."
} ```
  - `400 Bad Request`: Invalid code or password.

---

### 🔹 Change Password - TESTED OK

- **Endpoint**: `/auth/change-password`
- **Method**: POST
- **Description**: Change password using old and new credentials.
- **Headers**:
  - `Authorization`: Bearer token
- **Request Body**:
  ```json
  {
    "old_password": "OldPassword123!",
    "new_password": "NewPassword456!"
  }
  ```
- **Responses**:
  - `200 OK`: ```json {
    "message": "Password changed successfully."
}```
  - `400 Bad Request`: Failed to change.

---

### 🔹 Get User - TESTED OK

- **Endpoint**: `/auth/get-user`
- **Method**: GET
- **Description**: Get user details.
- **Headers**:
  - `Authorization`: Bearer token
- **Responses**:
  - `200 OK`: User info `{ "id", "email", "name" }`
  - `401 Unauthorized`: Invalid or expired token.

---

### 🔹 Delete User - TESTED OK

- **Endpoint**: `/auth/delete-user`
- **Method**: DELETE
- **Description**: Delete user account and data.
- **Headers**:
  - `Authorization`: Bearer token
- **Responses**:
  - `200 OK`: ```json {
    "message": "User 41fb85c0-1081-704a-d661-cf41d49dae10 and all related data deleted successfully."
} ```
  - `400 Bad Request`: Failed to delete.

---

## ⚙️ Error Codes 

- `4XX`: Client errors (bad input, auth failures)
- `5XX`: Server errors

---

## 🐳 Deployment

Build & run with Docker:

```bash
docker build -t auth-service .  && docker run -p 8000:8000 auth-service
```