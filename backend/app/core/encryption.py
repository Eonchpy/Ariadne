from __future__ import annotations

import base64
import json
from typing import Iterable

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings


_fernet: Fernet | None = None
SENSITIVE_KEYS = {"password", "pwd", "secret", "api_key", "token"}


def get_fernet() -> Fernet:
    global _fernet
    if _fernet:
        return _fernet
    key = settings.ENCRYPTION_KEY
    if not key:
        raise RuntimeError("ENCRYPTION_KEY is not set")
    # Allow raw 32-byte base64 strings or already base64 urlsafe key
    try:
        base64.urlsafe_b64decode(key)
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Invalid ENCRYPTION_KEY format") from exc
    return _fernet


def encrypt_value(value: str) -> str:
    f = get_fernet()
    token = f.encrypt(value.encode())
    return token.decode()


def decrypt_value(token: str) -> str:
    f = get_fernet()
    return f.decrypt(token.encode()).decode()


def encrypt_dict(data: dict, fields: Iterable[str] | None = None) -> dict:
    if not data:
        return data
    sensitive = set(fields) if fields else SENSITIVE_KEYS
    encrypted = {}
    for k, v in data.items():
        if v is None:
            encrypted[k] = v
            continue
        if k.lower() in sensitive and isinstance(v, str):
            encrypted[k] = {"__enc__": encrypt_value(v)}
        else:
            encrypted[k] = v
    return encrypted


def decrypt_dict(data: dict, fields: Iterable[str] | None = None) -> dict:
    if not data:
        return data
    sensitive = set(fields) if fields else SENSITIVE_KEYS
    decrypted = {}
    for k, v in data.items():
        if isinstance(v, dict) and "__enc__" in v:
            try:
                decrypted[k] = decrypt_value(v["__enc__"])
            except InvalidToken:
                decrypted[k] = None
        else:
            decrypted[k] = v
    return decrypted


def mask_dict(data: dict, fields: Iterable[str] | None = None) -> dict:
    if not data:
        return data
    sensitive = set(fields) if fields else SENSITIVE_KEYS
    masked = {}
    for k, v in data.items():
        if k.lower() in sensitive:
            masked[k] = "******" if v is not None else None
        else:
            masked[k] = v
    return masked
