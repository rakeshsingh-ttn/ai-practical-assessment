from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.backend.app.models.entities import TicketPriority, TicketStatus, UserRole


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    role: UserRole


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    description: str = Field(default="", max_length=5000)
    priority: TicketPriority
    created_by: int
    assigned_to: int | None = None


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=5000)
    priority: TicketPriority | None = None
    assigned_to: int | None = None


class TicketStatusUpdate(BaseModel):
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


class TicketListOut(BaseModel):
    items: list[TicketOut]
    total: int
    limit: int
    offset: int


class CommentCreate(BaseModel):
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
