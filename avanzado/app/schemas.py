from pydantic import BaseModel, BeforeValidator, Field, field_validator
from datetime import date, datetime
from enum import StrEnum
import re
from typing import Annotated, Any


class Priority(StrEnum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


_DATE_FORMAT = re.compile(r"\d{4}-\d{2}-\d{2}")


def _require_date_format(value: Any) -> Any:
    # Pydantic, por sí solo, acepta también "2026-10-01T00:00:00" o un 0
    # (1970-01-01). strict=True no sirve: FastAPI valida el body en modo Python
    # y ahí strict rechaza cualquier string.
    if value is None or (isinstance(value, date) and not isinstance(value, datetime)):
        return value
    if isinstance(value, str) and _DATE_FORMAT.fullmatch(value):
        return value
    raise ValueError("La fecha límite tiene que tener el formato AAAA-MM-DD")


DueDate = Annotated[date, BeforeValidator(_require_date_format)]


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool = False
    priority: Priority = Priority.MEDIA
    due_date: DueDate | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool | None = None
    priority: Priority | None = None
    due_date: DueDate | None = None

    # Omitida queda fuera por exclude_unset; mandada en null se rechaza, porque
    # model_copy no valida y terminaría como NULL en una columna NOT NULL.
    @field_validator("priority")
    @classmethod
    def _priority_not_null(cls, value: Priority | None) -> Priority:
        if value is None:
            raise ValueError("La prioridad no puede ser nula")
        return value


class TaskFilters(BaseModel):
    priority: Priority | None = None
    completed: bool | None = None

    # Un <select> con la opción "todas" manda ?priority= vacío: es sin filtro.
    @field_validator("*", mode="before")
    @classmethod
    def _empty_as_none(cls, value: Any) -> Any:
        return None if value == "" else value


class Task(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool
    created_at: datetime
    priority: Priority
    due_date: date | None
