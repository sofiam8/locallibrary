
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from ninja import Router, Status
from ninja.errors import HttpError

from .schemas import RefreshIn, SignupIn, TokenIn, TokenOut, UserOut
from .tokens import create_token_pair, decode_token


router = Router(tags=["auth"], auth=None)
tokens = Router(tags=["auth"], auth=None)


@router.post("/signup", response={201: UserOut})
def signup(request, payload: SignupIn):
    if User.objects.filter(username=payload.username).exists():
        raise HttpError(409, "This username is taken")

    try:
        validate_password(payload.password)
    except ValidationError as e:
        raise HttpError(400, " ".join(e.messages))

    user = User.objects.create_user(
        payload.username,
        password=payload.password,
    )

    return Status(201, user)


@tokens.post("/token", response=TokenOut, deprecated=True)
def obtain_token(request, payload: TokenIn):
    """Use POST /taskflow/api/v2/auth/token instead."""
    user = authenticate(
        username=payload.username,
        password=payload.password,
    )

    if user is None:
        raise HttpError(401, "Invalid username or password")

    return create_token_pair(user.id)


@tokens.post("/refresh", response=TokenOut, deprecated=True)
def refresh_token(request, payload: RefreshIn):
    """Use POST /taskflow/api/v2/auth/refresh instead."""
    claims = decode_token(payload.refresh, "refresh")

    if claims is None or not User.objects.filter(
        id=claims["sub"],
        is_active=True,
    ).exists():
        raise HttpError(401, "Invalid or expired refresh token")

    return create_token_pair(int(claims["sub"]))
