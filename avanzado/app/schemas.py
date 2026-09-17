from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class Priority(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool = False
    priority: Priority = Priority.media
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool | None = None
    priority: Priority | None = None
    due_date: date | None = None


class Task(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool
    priority: Priority
    due_date: date | None
    created_at: datetime
