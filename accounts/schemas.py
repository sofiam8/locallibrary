
from typing import Literal

from django.contrib.auth.models import User
from ninja import ModelSchema, Schema
from pydantic import Field


class UserOut(ModelSchema):
    display_name: str

    class Meta:
        model = User
        fields = ["id", "username"]

    @staticmethod
    def resolve_display_name(user):
        return user.get_full_name() or user.username


class SignupIn(Schema):
    username: str
    password: str


class TokenIn(Schema):
    username: str
    password: str


class RefreshIn(Schema):
    refresh: str


class TokenOut(Schema):
    access: str
    refresh: str


class OAuthTokenOut(Schema):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"]
    expires_in: int = Field(
        description="Seconds until the access token expires",
        examples=[900],
    )


class OAuthRefreshIn(Schema):
    refresh_token: str
