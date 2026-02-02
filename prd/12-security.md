# 12. Security Requirements

## 12.1 Authentication

| Requirement | Implementation |
|-------------|----------------|
| **Password Hashing** | bcrypt with cost factor 12 |
| **Session Management** | Server-side sessions with secure cookies |
| **Session Timeout** | 24 hours idle, 7 days absolute |
| **CSRF Protection** | Token-based CSRF protection on all forms |

## 12.2 API Security

| Requirement | Implementation |
|-------------|----------------|
| **Rate Limiting** | 100 requests/minute per IP |
| **Input Validation** | Pydantic models with strict validation |
| **SQL Injection** | Parameterized queries via SQLAlchemy ORM |
| **XSS Prevention** | Content Security Policy headers |

## 12.3 Secrets Management

```python
# app/config.py
from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    """Application settings with secure secret handling."""
    
    # Secrets are never logged or exposed
    SECRET_KEY: SecretStr
    DATABASE_URL: SecretStr
    GROCY_API_KEY: SecretStr
    LLM_API_KEY: SecretStr = SecretStr("")
    BRAVE_API_KEY: SecretStr = SecretStr("")
    GOUPC_API_KEY: SecretStr = SecretStr("")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

## 12.4 Network Security

| Requirement | Implementation |
|-------------|----------------|
| **TLS Termination** | At reverse proxy (Caddy/Traefik) |
| **Internal Communication** | HTTP within Docker network only |
| **Grocy API URL** | Separate internal vs external URLs |
| **CORS** | Restricted to configured origins |

## 12.5 API Key Authentication for External Access

```python
# app/api/auth.py
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify API key for external application access."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    valid_key = await validate_api_key(api_key)
    if not valid_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return valid_key
```

## 12.6 Security Checklist

- [ ] All secrets stored in environment variables
- [ ] Database credentials use strong passwords
- [ ] API keys have minimum required permissions
- [ ] TLS enabled for all external connections
- [ ] Session cookies marked as HttpOnly and Secure
- [ ] CORS configured to allow only trusted origins
- [ ] Rate limiting enabled on all endpoints
- [ ] Input validation on all user inputs
- [ ] Logs do not contain sensitive data
- [ ] Dependencies scanned for vulnerabilities

---

## Navigation

- **Previous:** [Schema Evolution](11-schema-evolution.md)
- **Next:** [Project Standards](13-project-standards.md)
- **Back to:** [README](README.md)
