import time

import jwt
import pytest

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.utils.text import escape_like, slugify


def test_slugify_vietnamese():
    assert slugify("Sofa Phòng Khách") == "sofa-phong-khach"
    assert slugify("Đèn trang trí & Đồ decor!") == "den-trang-tri-do-decor"
    assert slugify("   ") == ""


def test_escape_like():
    assert escape_like("50%_off") == "50\\%\\_off"


def test_password_hash_roundtrip():
    h = hash_password("Secret123")
    assert h != "Secret123" and h.startswith("$argon2")
    assert verify_password("Secret123", h)
    assert not verify_password("wrong", h)
    assert not verify_password("x", "not-a-hash")


def test_token_roundtrip_and_expiry():
    token, expires_in = create_access_token(42)
    assert expires_in == get_settings().access_token_expire_minutes * 60
    assert decode_access_token(token)["sub"] == "42"
    expired, _ = create_access_token(42, expires_minutes=-1)
    with pytest.raises(AuthenticationError) as e:
        decode_access_token(expired)
    assert e.value.code == "TOKEN_EXPIRED"


def test_token_tampering_and_alg_none():
    token, _ = create_access_token(1)
    with pytest.raises(AuthenticationError):
        decode_access_token(token[:-2] + "xx")
    forged = jwt.encode({"sub": "1", "exp": int(time.time()) + 100, "type": "access"}, "", algorithm="none")
    with pytest.raises(AuthenticationError):
        decode_access_token(forged)
    wrong_type = jwt.encode(
        {"sub": "1", "exp": int(time.time()) + 100, "type": "refresh"},
        get_settings().jwt_secret_key,
        algorithm="HS256",
    )
    with pytest.raises(AuthenticationError):
        decode_access_token(wrong_type)
