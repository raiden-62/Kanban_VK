from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
from typing import Any

import bcrypt

from app.core.config import get_settings


APP_TIMEZONE = timezone(timedelta(hours=3))


def _password_digest(password: str) -> bytes:
    return hashlib.sha256(password.encode("utf-8")).digest()


def verify_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(_password_digest(plain_password), password_hash.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(_password_digest(password), bcrypt.gensalt()).decode("utf-8")


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}")


def _json_bytes(data: dict[str, Any]) -> bytes:
    return json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    settings = get_settings()
    if settings.algorithm != "HS256":
        raise ValueError("Only HS256 JWT tokens are supported")
    expire = datetime.now(APP_TIMEZONE) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    header = {"alg": settings.algorithm, "typ": "JWT"}
    payload: dict[str, Any] = {"sub": str(subject), "exp": int(expire.timestamp())}
    signing_input = ".".join(
        [
            _base64url_encode(_json_bytes(header)),
            _base64url_encode(_json_bytes(payload)),
        ]
    )
    signature = hmac.new(
        settings.secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def decode_access_token(token: str) -> str | None:
    settings = get_settings()
    try:
        header_part, payload_part, signature_part = token.split(".", 2)
        signing_input = f"{header_part}.{payload_part}"
        expected_signature = hmac.new(
            settings.secret_key.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        actual_signature = _base64url_decode(signature_part)
        if not hmac.compare_digest(expected_signature, actual_signature):
            return None

        header = json.loads(_base64url_decode(header_part))
        if header.get("alg") != settings.algorithm:
            return None

        payload = json.loads(_base64url_decode(payload_part))
    except (ValueError, json.JSONDecodeError):
        return None

    expires_at = payload.get("exp")
    if not isinstance(expires_at, int):
        return None
    if datetime.now(APP_TIMEZONE).timestamp() >= expires_at:
        return None

    subject = payload.get("sub")
    return subject if isinstance(subject, str) else None
