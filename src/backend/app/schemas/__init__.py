from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from src.backend.app.models.entities import TicketPriority, TicketStatus, UserRole


def _datetime_to_second_precision(dt: datetime) -> datetime:
    return dt.replace(microsecond=0)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: UserRole


class TicketCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=3, max_length=120)
    description: str = Field(default="", max_length=5000)
    priority: TicketPriority
    created_by: int
    assigned_to: int | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if len(stripped) < 3:
            raise ValueError("String should have at least 3 characters")
        return stripped


class TicketUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=5000)
    priority: TicketPriority | None = None
    assigned_to: int | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if len(stripped) < 3:
            raise ValueError("String should have at least 3 characters")
        return stripped


class TicketStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: TicketStatus


class UserRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str


class TicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    priority: TicketPriority
    status: TicketStatus
    assigned_to: int | None
    created_by: int
    created_at: datetime
    updated_at: datetime
    creator: UserRef | None = None
    assignee: UserRef | None = None

    @field_serializer("created_at", "updated_at")
    def serialize_datetimes(self, dt: datetime) -> datetime:
        return _datetime_to_second_precision(dt)


class TicketListOut(BaseModel):
    items: list[TicketOut]
    total: int
    limit: int
    offset: int


class CommentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=1, max_length=2000)
    created_by: int

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Message must not be empty or whitespace-only")
        return stripped


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: int
    message: str
    created_by: int
    created_at: datetime
    author: UserRef | None = None

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime) -> datetime:
        return _datetime_to_second_precision(dt)
