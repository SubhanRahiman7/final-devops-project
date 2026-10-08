from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal["open", "in_progress", "resolved"]
Priority = Literal["low", "medium", "high", "urgent"]
Category = Literal["billing", "technical", "account", "other"]


class TicketBase(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    status: Status = "open"
    priority: Priority = "medium"
    category: Category = "technical"
    requester: str = Field(default="", max_length=120)
    assignee: str = Field(default="", max_length=100)


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    subject: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: Status | None = None
    priority: Priority | None = None
    category: Category | None = None
    requester: str | None = Field(default=None, max_length=120)
    assignee: str | None = Field(default=None, max_length=100)


class TicketOut(TicketBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class TicketStats(BaseModel):
    total: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    by_category: dict[str, int]
    resolution_rate: float
    open_urgent: int
