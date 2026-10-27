from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.core.config import get_settings
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_verifies_without_storing_plaintext():
    password = "Strong-test-password-123"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_token_contains_subject_and_role_and_round_trips():
    token = create_access_token("42", "employee")
    decoded = decode_access_token(token)
    assert decoded["sub"] == "42"
    assert decoded["role"] == "employee"


def test_expired_token_is_rejected():
    settings = get_settings()
    token = jwt.encode(
        {"sub": "42", "role": "employee", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)

