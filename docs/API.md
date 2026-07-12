# CarbonTracker API Reference (v1.0.0)

Base URL: https://kkk-harshan-sona.onrender.com

---

## 1. Authentication Endpoints

### 1.1 User Registration
*   **URL**: `/auth/register`
*   **Method**: `POST`
*   **Payload**:
    ```json
    {
      "username": "user123",
      "email": "user@example.com",
      "password": "secure_password"
    }
    ```
*   **Response (`201 Created`)**:
    ```json
    {
      "success": true,
      "message": "User registered successfully"
    }
    ```

### 1.2 User Login
*   **URL**: `/auth/login`
*   **Method**: `POST`
*   **Payload**:
    ```json
    {
      "email": "user@example.com",
      "password": "secure_password"
    }
    ```
*   **Response (`200 OK`)**:
    ```json
    {
      "access_token": "jwt_access_token_string",
      "refresh_token": "jwt_refresh_token_string",
      "token_type": "bearer"
    }
    ```

---

## 2. Activity Tracker Endpoints

### 2.1 Log Natural Language Activity
*   **URL**: `/activity`
*   **Method**: `POST`
*   **Headers**: `Authorization: Bearer <access_token>`
*   **Payload**:
    ```json
    {
      "input_text": "drove 18 km in my car"
    }
    ```
*   **Response (`201 Created`)**:
    ```json
    {
      "id": 452,
      "input_text": "drove 18 km in my car",
      "calculated_value": 3.06,
      "category": "transport",
      "item": "car",
      "quantity": 18.0,
      "unit": "km",
      "logged_at": "2026-07-12T11:27:00Z"
    }
    ```

### 2.2 Get Activity History (Paginated)
*   **URL**: `/activity/history?limit=20&offset=0`
*   **Method**: `GET`
*   **Headers**: `Authorization: Bearer <access_token>`
*   **Response (`200 OK`)**:
    ```json
    [
      {
        "id": 452,
        "input_text": "drove 18 km in my car",
        "calculated_value": 3.06,
        "category": "transport"
      }
    ]
    ```
