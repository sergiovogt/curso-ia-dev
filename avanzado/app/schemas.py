from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Prioridad(StrEnum):
    alta = "alta"
    media = "media"
    baja = "baja"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool = False
    prioridad: Prioridad = Prioridad.media
    fecha_limite: date | None = None


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool | None = None


class Task(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool
    prioridad: Prioridad
    fecha_limite: date | None
    created_at: datetime
