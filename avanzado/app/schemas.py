from enum import StrEnum

from pydantic import BaseModel, Field, field_validator
from datetime import datetime


class Priority(StrEnum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool = False
    priority: Priority = Priority.MEDIA


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool | None = None
    priority: Priority | None = None

    @field_validator("priority")
    @classmethod
    def priority_no_nula(cls, value: Priority | None) -> Priority:
        # Solo corre si el campo vino en el body: omitirlo sigue siendo válido.
        if value is None:
            raise ValueError("La prioridad no puede ser nula")
        return value


class Task(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool
    created_at: datetime
    priority: Priority
