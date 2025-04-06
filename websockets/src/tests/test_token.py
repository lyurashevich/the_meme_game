from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from ..security.auth import (
    ALGORITHM,
    SECRET_KEY,
    get_current_user,
    verify_jwt,
)


@pytest.fixture
def valid_token():
    payload = {
        "sub": "12345",
        "name": "test",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def expired_token():
    payload = {
        "sub": "12345",
        "name": "test",
        "iat": datetime.now(timezone.utc) - timedelta(minutes=20),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=15),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def invalid_token():
    return "invaid.token.here"


def test_verify_jwt_valid_token(valid_token):
    payload = verify_jwt(valid_token)
    assert payload["sub"] == "12345"
    assert payload["name"] == "test"


def test_verify_jwt_expired_token(expired_token):
    with pytest.raises(HTTPException) as e:
        verify_jwt(expired_token)

    assert e.value.status_code == 401
    assert e.value.detail == "token expired"


def test_verify_jwt_invalid_token(invalid_token):
    with pytest.raises(HTTPException) as e:
        verify_jwt(invalid_token)

    assert e.value.status_code == 401
    assert e.value.detail == "invalid token"


def test_get_current_user_valid_token(valid_token):
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=valid_token)
    payload = get_current_user(credentials)
    assert payload["sub"] == "12345"
    assert payload["name"] == "test"


def test_get_current_user_expired_token(expired_token):
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=expired_token
    )
    with pytest.raises(HTTPException) as e:
        get_current_user(credentials)
    assert e.value.status_code == 401
    assert e.value.detail == "token expired"


def test_get_current_user_invalid_token(invalid_token):
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials=invalid_token
    )
    with pytest.raises(HTTPException) as e:
        get_current_user(credentials)
    assert e.value.status_code == 401
    assert e.value.detail == "invalid token"
