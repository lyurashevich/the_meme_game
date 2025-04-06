import os

import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, Security, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

load_dotenv()

SECRET_KEY = os.getenv("DJANGO_JWT_SECRET_KEY", "default_jwt_key")
ALGORITHM = "HS256"


security = HTTPBearer()


def verify_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token"
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    return verify_jwt(credentials.credentials)
