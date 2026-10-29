
import base64
import hashlib
import hmac
import json
import time

from django.conf import settings


ACCESS_TOKEN_LIFETIME = 15 * 60
REFRESH_TOKEN_LIFETIME = 7 * 24 * 60 * 60


def b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(
        data + "=" * (-len(data) % 4)
    )


def sign(message: str) -> str:
    digest = hmac.new(
        settings.SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256,
    ).digest()
    return b64encode(digest)


def create_token(user_id: int, token_type: str, lifetime: int) -> str:
    header = b64encode(
        json.dumps({"alg": "HS256", "typ": "JWT"}).encode()
    )

    claims = {
        "sub": str(user_id),
        "type": token_type,
        "exp": int(time.time()) + lifetime,
    }

    payload = b64encode(json.dumps(claims).encode())

    return f"{header}.{payload}.{sign(f'{header}.{payload}')}"


def decode_token(token: str, token_type: str) -> dict | None:
    try:
        header, payload, signature = token.split(".")

        if not hmac.compare_digest(
            signature.encode(),
            sign(f"{header}.{payload}").encode(),
        ):
            return None

        claims = json.loads(b64decode(payload))

        if claims["type"] != token_type:
            return None

        if claims["exp"] < time.time():
            return None

        return claims

    except (ValueError, KeyError, TypeError, UnicodeDecodeError):
        return None


def create_token_pair(user_id: int) -> dict:
    return {
        "access": create_token(
            user_id,
            "access",
            ACCESS_TOKEN_LIFETIME,
        ),
        "refresh": create_token(
            user_id,
            "refresh",
            REFRESH_TOKEN_LIFETIME,
        ),
    }
