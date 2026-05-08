from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ItemType(str, Enum):
    TASK = "task"
    APPOINTMENT = "appointment"
    REMINDER = "reminder"


class ItemStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class WorkItemCreateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(
        ..., description="Work item title (e.g. 'Call mom', 'Dentist appointment')", min_length=1, max_length=500
    )
    type: ItemType = Field(..., description="Item type: task, appointment, or reminder")
    description: Optional[str] = Field(default=None, max_length=5000, description="Detailed notes or description")
    priority: Optional[int] = Field(default=None, ge=1, le=5, description="Priority: 1 (highest) to 5 (lowest)")
    due_date: Optional[str] = Field(default=None, description="ISO 8601 UTC due date (e.g. '2026-05-07T15:00:00Z')")
    reminder_at: Optional[str] = Field(
        default=None, description="ISO 8601 UTC time to trigger reminder (e.g. '2026-05-07T14:00:00Z')"
    )
    start_time: Optional[str] = Field(
        default=None, description="ISO 8601 UTC start time (appointments only)"
    )
    end_time: Optional[str] = Field(default=None, description="ISO 8601 UTC end time (appointments only)")
    location: Optional[str] = Field(default=None, max_length=500, description="Physical or virtual location")
    participants: Optional[list[str]] = Field(default=None, description="List of participant identifiers")
    idempotency_key: Optional[str] = Field(default=None, description="UUID for deduplication")


class WorkItemUpdateInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    description: Optional[str] = Field(default=None, max_length=5000)
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    due_date: Optional[str] = Field(default=None)
    reminder_at: Optional[str] = Field(default=None)
    start_time: Optional[str] = Field(default=None)
    end_time: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None, max_length=500)
    participants: Optional[list[str]] = Field(default=None)
    idempotency_key: Optional[str] = Field(default=None)


class WorkItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    type: ItemType
    status: ItemStatus
    description: Optional[str] = None
    priority: Optional[int] = None
    due_date: Optional[str] = None
    reminder_at: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    participants: Optional[list[str]] = None
    created_at: str
    updated_at: str
