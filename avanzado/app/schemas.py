from enum import StrEnum

from pydantic import BaseModel, Field, field_validator
from datetime import date, datetime


class Priority(StrEnum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool = False
    priority: Priority = Priority.MEDIA
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    completed: bool | None = None
    priority: Priority | None = None
    due_date: date | None = None

    @field_validator("priority")
    @classmethod
    def priority_no_nula(cls, value: Priority | None) -> Priority:
        # Solo corre si el campo vino en el body: omitirlo sigue siendo válido.
        if value is None:
            raise ValueError("La prioridad no puede ser nula")
        return value


class SortBy(StrEnum):
    PRIORITY = "priority"
    DUE_DATE = "due_date"


class TaskFilters(BaseModel):
    priority: Priority | None = None
    completed: bool | None = None
    overdue: bool = False
    sort_by: SortBy | None = None

    @field_validator("priority", "completed", "sort_by", mode="before")
    @classmethod
    def vacio_es_sin_filtro(cls, value: object) -> object:
        # Las opciones "todas" del form de la página mandan el parámetro vacío.
        return None if value == "" else value

    @property
    def is_active(self) -> bool:
        return self.priority is not None or self.completed is not None or self.overdue


class Task(BaseModel):
    id: int
    title: str
    description: str | None
    completed: bool
    created_at: datetime
    priority: Priority
    due_date: date | None

    @property
    def is_overdue(self) -> bool:
        # Misma regla que el filtro overdue del repositorio. Property común: no se serializa.
        return not self.completed and self.due_date is not None and self.due_date < date.today()
