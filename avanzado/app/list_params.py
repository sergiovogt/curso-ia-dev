from collections.abc import Mapping
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, field_validator, model_validator

from app.schemas import Prioridad


class OrdenCampo(StrEnum):
    prioridad = "prioridad"
    fecha_limite = "fecha_limite"


class OrdenDir(StrEnum):
    asc = "asc"
    desc = "desc"


class TaskListParams(BaseModel):
    prioridad: list[Prioridad] | None = None
    fecha_desde: date | None = None
    fecha_hasta: date | None = None
    vencidas: bool = False
    sin_fecha: bool = False
    orden: OrdenCampo | None = None
    dir: OrdenDir = OrdenDir.asc

    @field_validator("prioridad", mode="before")
    @classmethod
    def parse_prioridad_csv(cls, value: object) -> object:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            items = [part.strip() for part in value.split(",") if part.strip()]
            return items or None
        if isinstance(value, list) and len(value) == 1 and isinstance(value[0], str) and "," in value[0]:
            items = [part.strip() for part in value[0].split(",") if part.strip()]
            return items or None
        return value

    @model_validator(mode="after")
    def validate_date_range(self) -> "TaskListParams":
        if (
            self.fecha_desde is not None
            and self.fecha_hasta is not None
            and self.fecha_desde > self.fecha_hasta
        ):
            raise ValueError("fecha_desde no puede ser posterior a fecha_hasta")
        return self


def _parse_bool(value: str | None) -> bool:
    if value is None or value == "":
        return False
    return value.lower() in {"1", "true", "yes", "on"}


def task_list_params_from_query(query_params: Mapping[str, str]) -> TaskListParams:
    data: dict[str, object] = {}

    if "prioridad" in query_params:
        data["prioridad"] = query_params.get("prioridad")

    if "fecha_desde" in query_params:
        data["fecha_desde"] = query_params.get("fecha_desde") or None

    if "fecha_hasta" in query_params:
        data["fecha_hasta"] = query_params.get("fecha_hasta") or None

    if "vencidas" in query_params:
        data["vencidas"] = _parse_bool(query_params.get("vencidas"))

    if "sin_fecha" in query_params:
        data["sin_fecha"] = _parse_bool(query_params.get("sin_fecha"))

    if "orden" in query_params:
        data["orden"] = query_params.get("orden") or None

    if "dir" in query_params:
        data["dir"] = query_params.get("dir") or OrdenDir.asc

    return TaskListParams.model_validate(data)
