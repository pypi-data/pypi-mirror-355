from pydantic import Field, BeforeValidator
from typing import Annotated, Optional
from .base import CommandType, BaseCommand


class LoginGoogleAccount(BaseCommand):
    email: Optional[str] = Field(
        default=None,
        examples=["user@example.com"],
        description="The email of the Google account, if None will get from bot env vars",
    )
    password: Optional[str] = Field(
        default=None,
        examples=["password123"],
        description="The password of the Google account, if None will get from bot env vars",
    )
    type: Annotated[
        CommandType, BeforeValidator(lambda _: CommandType.LOGIN_GOOGLE_ACCOUNT)
    ] = Field(init=False, default=CommandType.LOGIN_GOOGLE_ACCOUNT, frozen=True)
