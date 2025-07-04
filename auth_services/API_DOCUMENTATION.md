# API Documentation for Auth Microservice

## Overview

This document provides an overview of the API endpoints available in the Auth Microservice. Each endpoint is described with its purpose, request payload, and possible responses.

## Endpoints

### Health Check

- **Endpoint**: `/`
- **Method**: GET
- **Description**: Check the health status of the service.
- **Response**: 
  - 200 OK: `{"health": "All Good"}`

### Sign Up

- **Endpoint**: `/signup`
- **Method**: POST
- **Description**: Register a new user.
- **Request Payload**: 
  - `email`: string
  - `password`: string
  - `name`: string
- **Response**: 
  - 201 Created: User registered successfully.
  - 400 Bad Request: Signup failed. Check email or password format.
  - 409 Conflict: Email already exists.

### Login

- **Endpoint**: `/login`
- **Method**: POST
- **Description**: Authenticate a user.
- **Request Payload**: 
  - `email`: string
  - `password`: string
- **Response**: 
  - 200 OK: Returns authentication tokens.
  - 401 Unauthorized: Invalid email or password.

### Refresh Token

# Currently not working

- **Endpoint**: `/refresh-token`
- **Method**: POST
- **Description**: Refresh authentication tokens.
- **Request Payload**: 
  - `email`: string
  - `refresh_token`: string
- **Response**: 
  - 200 OK: Returns new authentication tokens.
  - 401 Unauthorized: Invalid or expired refresh token.

### Logout

- **Endpoint**: `/logout`
- **Method**: POST
- **Description**: Log out a user.
- **Request Header**: 
  - `Authorization`: Bearer token
- **Response**: 
  - 200 OK: User logged out successfully.
  - 401 Unauthorized: Failed to logout. Invalid token.

### Confirm Sign Up

- **Endpoint**: `/confirm-signup`
- **Method**: POST
- **Description**: Confirm user registration.
- **Request Payload**: 
  - `email`: string
  - `code`: string
- **Response**: 
  - 200 OK: User confirmed successfully.
  - 400 Bad Request: Failed to confirm sign up. Invalid code or user.

### Resend Confirmation Code

- **Endpoint**: `/resend-confirmation-code`
- **Method**: POST
- **Description**: Resend the confirmation code to the user.
- **Request Payload**: 
  - `email`: string
- **Response**: 
  - 200 OK: Confirmation code resent successfully.
  - 400 Bad Request: Failed to resend confirmation code.

### Forgot Password

- **Endpoint**: `/forgot-password`
- **Method**: POST
- **Description**: Initiate forgot password process.
- **Request Payload**: 
  - `email`: string
- **Response**: 
  - 200 OK: Forgot password code sent successfully.
  - 400 Bad Request: Failed to send forgot password code.

### Confirm Forgot Password

- **Endpoint**: `/confirm-forgot-password`
- **Method**: POST
- **Description**: Confirm password reset.
- **Request Payload**: 
  - `email`: string
  - `code`: string
  - `new_password`: string
- **Response**: 
  - 200 OK: Password reset successful.
  - 400 Bad Request: Failed to confirm forgot password. Check code and password format.

### Change Password

- **Endpoint**: `/change-password`
- **Method**: POST
- **Description**: Change user password.
- **Request Payload**: 
  - `old_password`: string
  - `new_password`: string
- **Request Header**: 
  - `Authorization`: Bearer token
- **Response**: 
  - 200 OK: Password changed successfully.
  - 400 Bad Request: Failed to change password. Check current or new password.

### Get User

- **Endpoint**: `/get-user`
- **Method**: GET
- **Description**: Retrieve user details.
- **Request Header**: 
  - `Authorization`: Bearer token
- **Response**: 
  - 200 OK: Returns user details.
  - 401 Unauthorized: Failed to retrieve user. Invalid or expired token.

### Delete User

- **Endpoint**: `/delete-user`
- **Method**: DELETE
- **Description**: Delete a user and all related data.
- **Request Header**: 
  - `Authorization`: Bearer token
- **Response**: 
  - 200 OK: User and all related data deleted successfully.
  - 400 Bad Request: Failed to delete user and related data.
