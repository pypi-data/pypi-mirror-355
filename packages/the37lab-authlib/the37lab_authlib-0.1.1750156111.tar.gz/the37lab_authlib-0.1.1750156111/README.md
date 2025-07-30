# AuthLib

A Python authentication library that provides JWT, OAuth2, and API token authentication with PostgreSQL backend. This library is designed for seamless integration with Flask applications and provides a robust set of endpoints and utilities for user management, authentication, and API token handling.

## Table of Contents
- [AuthLib](#authlib)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Quick Start](#quick-start)
  - [Configuration](#configuration)
    - [Required Parameters](#required-parameters)
    - [Optional Parameters](#optional-parameters)
      - [Example `oauth_config`:](#example-oauth_config)
  - [API Endpoints](#api-endpoints)
    - [Authentication](#authentication)
    - [User Management](#user-management)
    - [API Tokens](#api-tokens)
  - [Authentication Flow](#authentication-flow)
  - [User Object](#user-object)
  - [Token Management](#token-management)
  - [Development](#development)
    - [Setup](#setup)
    - [Database Setup](#database-setup)
    - [Running Tests](#running-tests)

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from flask import Flask
from authlib import AuthManager

app = Flask(__name__)

auth = AuthManager(
    app=app,
    db_dsn="postgresql://user:pass@localhost/dbname",
    jwt_secret="your-secret-key",
    oauth_config={
        "google": {
            "client_id": "your-client-id",
            "client_secret": "your-client-secret"
        }
    }
)

@app.route("/protected")
@auth.require_auth(roles=["admin"])
def protected_route():
    return "Protected content"
```

## Configuration

### Required Parameters
- `app`: Flask application instance
- `db_dsn`: PostgreSQL connection string
- `jwt_secret`: Secret key for JWT signing

### Optional Parameters
- `oauth_config`: Dictionary of OAuth provider configurations (see below)
- `token_expiry`: JWT token expiry time in seconds (default: 3600)
- `refresh_token_expiry`: Refresh token expiry time in seconds (default: 2592000)

#### Example `oauth_config`:
```python
{
    "google": {
        "client_id": "...",
        "client_secret": "..."
    },
    "github": {
        "client_id": "...",
        "client_secret": "..."
    }
}
```

## API Endpoints

### Authentication
- `POST /v1/users/login` - Login with username/password
  - **Request:** `{ "username": "string", "password": "string" }`
  - **Response:** `{ "token": "jwt", "refresh_token": "jwt", "user": { ... } }`
- `POST /v1/users/login/oauth` - Get OAuth redirect URL
  - **Request:** `{ "provider": "google|github|..." }`
  - **Response:** `{ "redirect_url": "string" }`
- `GET /v1/users/login/oauth2callback` - OAuth callback
  - **Query Params:** `code`, `state`, `provider`
  - **Response:** `{ "token": "jwt", "refresh_token": "jwt", "user": { ... } }`
- `POST /v1/users/token-refresh` - Refresh JWT token
  - **Request:** `{ "refresh_token": "jwt" }`
  - **Response:** `{ "token": "jwt", "refresh_token": "jwt" }`

### User Management
- `POST /v1/users/register` - Register new user
  - **Request:** `{ "username": "string", "password": "string", "email": "string", ... }`
  - **Response:** `{ "user": { ... }, "token": "jwt", "refresh_token": "jwt" }`
- `GET /v1/users/login/profile` - Get user profile
  - **Auth:** Bearer JWT
  - **Response:** `{ "user": { ... } }`
- `GET /v1/users/roles` - Get available roles
  - **Response:** `[ "admin", "user", ... ]`

### API Tokens
- `POST /v1/users/{user}/api-tokens` - Create API token
  - **Request:** `{ "name": "string", "scopes": [ ... ] }`
  - **Response:** `{ "token": "string", "id": "uuid", ... }`
- `GET /v1/users/{user}/api-tokens` - List API tokens
  - **Response:** `[ { "id": "uuid", "name": "string", ... } ]`
- `DELETE /v1/users/{user}/api-tokens/{token_id}` - Delete API token
  - **Response:** `{ "success": true }`

## Authentication Flow

1. **Login:**
   - User submits credentials to `/v1/users/login`.
   - Receives JWT and refresh token.
2. **Token Refresh:**
   - Use `/v1/users/token-refresh` with refresh token to get new JWT.
3. **OAuth:**
   - Get redirect URL from `/v1/users/login/oauth`.
   - Complete OAuth flow via `/v1/users/login/oauth2callback`.
4. **Protected Routes:**
   - Use `@auth.require_auth()` decorator to protect Flask routes.

## User Object

The user object returned by the API typically includes:
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "roles": ["user", "admin"],
  "created_at": "timestamp",
  "last_login": "timestamp"
}
```

## Token Management
- **JWT:** Used for authenticating API requests. Include in `Authorization: Bearer <token>` header.
- **Refresh Token:** Used to obtain new JWTs without re-authenticating.
- **API Tokens:** Long-lived tokens for programmatic access, managed per user.

## Development

### Setup
1. Clone the repository
2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
```
3. Install dependencies:
```bash
pip install -e ".[dev]"
```

### Database Setup
```bash
createdb authlib
python -m authlib.cli db init
```

### Running Tests
```bash
pytest
```
