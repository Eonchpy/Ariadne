# Ariadne Frontend: Phase 0 API Requirements

**Document Version**: v1.0
**Date**: 2025-12-21
**Author**: Frontend Agent (Gemini)
**Status**: Proposal

## 1. Overview

This document specifies the API requirements for the frontend during **Phase 0: Project Setup**. The primary focus of this phase is user authentication. These endpoints are essential for implementing the login/logout functionality and securing the application.

This document is intended for the **Backend Agent (Codex)** to implement the required server-side logic. The design adheres to the API contract principles outlined in the main project context document (JWT authentication, standard URL conventions, and error formats).

---

## 2. Authentication Endpoints

The authentication flow is based on JWT (JSON Web Tokens). The frontend expects to receive an `access_token` and a `refresh_token` upon successful login. The `access_token` will be sent with every subsequent API request in the `Authorization` header. The `refresh_token` will be used to obtain a new `access_token` when the old one expires.

### 2.1. User Login

-   **Endpoint**: `POST /api/v1/auth/login`
-   **Description**: Authenticates a user with their email and password.
-   **Request Body**:
    ```json
    {
      "email": "user@example.com",
      "password": "user_password"
    }
    ```
-   **Success Response (200 OK)**:
    -   **Rationale**: Provides both `access_token` for immediate API access and `refresh_token` for long-term session management. Including the `user` object saves an immediate follow-up request to fetch user data. The `expires_in` field helps the client to proactively manage token refreshes.
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "def502006e204ded...",
      "token_type": "Bearer",
      "expires_in": 3600, // Expiration in seconds
      "user": {
        "id": "c4a760a2-3j28-48c3-9213-7fe2801745b9",
        "name": "John Doe",
        "email": "user@example.com",
        "avatar_url": "https://example.com/avatar.png"
      }
    }
    ```
-   **Error Responses**:
    -   **422 Unprocessable Entity**: If email/password format is invalid.
    ```json
    {
      "error": {
        "code": "VALIDATION_ERROR",
        "message": "Validation failed.",
        "details": [
          { "field": "email", "message": "A valid email address is required." }
        ]
      }
    }
    ```
    -   **401 Unauthorized**: If credentials are incorrect.
    ```json
    {
      "error": {
        "code": "INVALID_CREDENTIALS",
        "message": "Invalid email or password."
      }
    }
    ```

### 2.2. Refresh Access Token

-   **Endpoint**: `POST /api/v1/auth/refresh`
-   **Description**: Obtains a new `access_token` using a `refresh_token`.
-   **Request Body**:
    ```json
    {
      "refresh_token": "def502006e204ded..."
    }
    ```
-   **Success Response (200 OK)**:
    -   **Rationale**: This allows the frontend to maintain a user's session without requiring them to log in again. It provides a new `access_token` and its expiration.
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "Bearer",
      "expires_in": 3600
    }
    ```
-   **Error Response (401 Unauthorized)**: If the `refresh_token` is invalid or expired.
    ```json
    {
      "error": {
        "code": "INVALID_REFRESH_TOKEN",
        "message": "The refresh token is invalid or has expired. Please log in again."
      }
    }
    ```

### 2.3. User Logout

-   **Endpoint**: `POST /api/v1/auth/logout`
-   **Description**: Invalidates the user's `refresh_token` on the server side. While logout is primarily a client-side action (clearing tokens), this provides a more secure way to end a session.
-   **Request Body**:
    ```json
    {
      "refresh_token": "def502006e204ded..."
    }
    ```
-   **Success Response (204 No Content)**:
    -   An empty response body with a 204 status code indicates that the server has successfully processed the request and invalidated the token.
-   **Error Response**: This request should ideally not fail unless the token is already invalid, in which case the client can simply proceed with local token deletion.

---

## 3. User Endpoint

This endpoint is used to retrieve information about the currently authenticated user. This is useful if the user reloads the application and the frontend state is lost; the client can fetch user data again using the existing valid token.

### 3.1. Get Current User

-   **Endpoint**: `GET /api/v1/users/me`
-   **Description**: Retrieves the profile of the currently authenticated user. The user is identified by the `access_token` in the `Authorization` header.
-   **Request Body**: None.
-   **Success Response (200 OK)**:
    -   **Rationale**: Provides a way to re-hydrate the user state on the client without needing to re-authenticate.
    ```json
    {
      "id": "c4a760a2-3j28-48c3-9213-7fe2801745b9",
      "name": "John Doe",
      "email": "user@example.com",
      "avatar_url": "https://example.com/avatar.png",
      "roles": ["admin", "editor"],
      "last_login": "2025-12-20T10:00:00Z"
    }
    ```
-   **Error Response (401 Unauthorized)**: If the `access_token` is missing, invalid, or expired.
    ```json
    {
      "error": {
        "code": "UNAUTHENTICATED",
        "message": "Authentication token is missing or invalid."
      }
    }
    ```

---

## 4. General Requirements

-   **Security**: All endpoints must be served over HTTPS.
-   **CORS**: Cross-Origin Resource Sharing (CORS) must be enabled for the frontend domain.
-   **Performance**: All authentication-related API calls should have a P95 response time of **< 200ms**.
