import time

import jwt
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_signing_key: str = "local-dev-signing-key"
    client_id: str = "local-dev-client-id"
    client_secret: str = "local-dev-client-secret"
    token_ttl_seconds: int = 3600

    class Config:
        env_prefix = ""


settings = Settings()


def issue_token(client_id: str) -> dict:
    now = int(time.time())
    token = jwt.encode(
        {
            "sub": client_id,
            "iat": now,
            "exp": now + settings.token_ttl_seconds,
            "scope": "nsc:read",
        },
        settings.jwt_signing_key,
        algorithm="HS256",
    )
    return {"access_token": token, "token_type": "Bearer", "expires_in": settings.token_ttl_seconds}


def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.jwt_signing_key, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
