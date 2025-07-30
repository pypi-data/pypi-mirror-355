# AuthLib

A Python authentication library that provides JWT, OAuth2, and API token authentication with PostgreSQL backend.

## Table of Contents
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Development](#development)

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
- `oauth_config`: Dictionary of OAuth provider configurations
- `token_expiry`: JWT token expiry time in seconds (default: 3600)
- `refresh_token_expiry`: Refresh token expiry time in seconds (default: 2592000)

## API Endpoints

### Authentication
- `POST /v1/users/login` - Login with username/password
- `POST /v1/users/login/oauth` - Get OAuth redirect URL
- `GET /v1/users/login/oauth2callback` - OAuth callback
- `POST /v1/users/token-refresh` - Refresh JWT token

### User Management
- `POST /v1/users/register` - Register new user
- `GET /v1/users/login/profile` - Get user profile
- `GET /v1/users/roles` - Get available roles

### API Tokens
- `POST /v1/users/{user}/api-tokens` - Create API token
- `GET /v1/users/{user}/api-tokens` - List API tokens
- `DELETE /v1/users/{user}/api-tokens/{token_id}` - Delete API token

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
