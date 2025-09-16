# from datetime import datetime, timedelta, timezone
# from typing import Optional

# import jwt
# from fastapi.testclient import TestClient
# from security.auth import ALGORITHM, SECRET_KEY

# from ..main import app

# client = TestClient(app)


# def create_test_token(data: dict, expires_delta: Optional[timedelta] = None):
#     payload = data.copy()

#     if expires_delta:
#         expire = datetime.now(timezone.utc) + expires_delta
#     else:
#         expire = datetime.now(timezone.utc) + timedelta(minutes=15)

#     payload.update({"exp": expire})
#     token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
#     return token


# def test_protected_valid_token():
#     token = create_test_token({"sub": "test"})

#     response = client.get(
#         "token/protected", headers={"Authorization": f"Bearer {token}"}
#     )

#     assert response.status_code == 200
#     assert "'sub': 'test'" in response.json()["message"]


# def test_protected_invalid_token():
#     invalid_token = "invalid_token"

#     response = client.get(
#         "token/protected", headers={"Authorization": f"Bearer {invalid_token}"}
#     )

#     assert response.status_code == 401
#     assert response.json() == {"detail": "invalid token"}


# def test_protected_expired_token():
#     expired_token = create_test_token(
#         {"sub": "test"}, expires_delta=timedelta(minutes=-30)
#     )

#     response = client.get(
#         "token/protected", headers={"Authorization": f"Bearer {expired_token}"}
#     )

#     assert response.status_code == 401
#     assert response.json() == {"detail": "token expired"}


# def test_protected_no_token():
#     response = client.get("/token/protected")
#     assert response.status_code == 403
#     assert response.json() == {"detail": "Not authenticated"}
