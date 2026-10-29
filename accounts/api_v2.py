
from ninja import Router

from . import api as v1
from .schemas import OAuthRefreshIn, OAuthTokenOut, RefreshIn, TokenIn
from .tokens import ACCESS_TOKEN_LIFETIME


tokens = Router(tags=["auth"], auth=None)


def oauth_response(pair):
    return {
        "access_token": pair["access"],
        "refresh_token": pair["refresh"],
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_LIFETIME,
    }


@tokens.post("/token", response=OAuthTokenOut)
def obtain_token(request, payload: TokenIn):
    """Exchange a username and password for an access and a refresh token."""
    return oauth_response(v1.obtain_token(request, payload))


@tokens.post("/refresh", response=OAuthTokenOut)
def refresh_token(request, payload: OAuthRefreshIn):
    """Exchange a refresh token for a new pair of tokens."""
    return oauth_response(
        v1.refresh_token(
            request,
            RefreshIn(refresh=payload.refresh_token),
        )
    )
