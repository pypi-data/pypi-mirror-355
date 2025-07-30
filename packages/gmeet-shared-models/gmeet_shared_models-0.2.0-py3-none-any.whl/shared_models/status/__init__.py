from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime


class BotStatus(Enum):
    INITIALIZING = (0, "initializing")
    INITIALIZED = (1, "initialized")

    LOGGING_GOOGLE = (2, "logging_google")
    LOGGED_GOOGLE = (3, "logged_google")

    CONNECTING_MEET = (4, "connecting_meet")
    CONNECTED_MEET = (5, "connected_meet")

    RECORDING_STARTED = (6, "recording_started")
    RECORDING_STOPPED = (7, "recording_stopped")

    DEAD = (8, "dead")

    ERROR = (9, "error")

    @property
    def code(self):
        return self.value[0]

    @property
    def label(self):
        return self.value[1]

    def __str__(self):
        return self.label


class StatusMessage(BaseModel):
    status: BotStatus = Field(..., description="The current status of the bot")
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="The timestamp when the status was last updated",
    )
    google_account_email: str = Field(
        ..., description="The email of the Google account associated with the bot"
    )
    details: dict = Field(
        default_factory=dict, description="Additional details about the status, if any"
    )
