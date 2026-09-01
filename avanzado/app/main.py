from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from app.database import init_db
from app.dates import today_app
from app.list_params import TaskListParams, task_list_params_from_query
from app.repository import TaskRepository
from app.schemas import Prioridad, Task, TaskCreate, TaskUpdate

repo = TaskRepository()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


def get_task_list_params(request: Request) -> TaskListParams:
    try:
        return task_list_params_from_query(request.query_params)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="CRUD de Tareas", version="1.0.0", lifespan=lifespan)


# --- UI (páginas server-rendered) ---


@app.get("/", response_class=HTMLResponse)
def index(
    request: Request,
    params: Annotated[TaskListParams, Depends(get_task_list_params)],
) -> HTMLResponse:
    tasks = repo.list_filtered(params)
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "tasks": tasks,
            "today": today_app(),
            "filters": params,
        },
    )


@app.post("/ui/tasks")
def ui_create_task(
    title: str = Form(...),
    description: str = Form(""),
    prioridad: Prioridad = Form(Prioridad.media),
    fecha_limite: str = Form(""),
) -> RedirectResponse:
    parsed_fecha: date | None = None
    if fecha_limite.strip():
        try:
            parsed_fecha = date.fromisoformat(fecha_limite.strip())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="fecha_limite debe tener formato YYYY-MM-DD",
            ) from exc

    repo.create(
        TaskCreate(
            title=title,
            description=description or None,
            prioridad=prioridad,
            fecha_limite=parsed_fecha,
        )
    )
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/ui/tasks/{task_id}/complete")
def ui_complete_task(task_id: int) -> RedirectResponse:
    repo.mark_complete(task_id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/ui/tasks/{task_id}/delete")
def ui_delete_task(task_id: int) -> RedirectResponse:
    repo.delete(task_id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


# --- API JSON ---


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> Task:
    return repo.create(payload)


@app.get("/tasks", response_model=list[Task])
def list_tasks(params: Annotated[TaskListParams, Depends(get_task_list_params)]) -> list[Task]:
    return repo.list_filtered(params)


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int) -> Task:
    task = repo.get_by_id(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea con id {task_id} no encontrada",
        )
    return task


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate) -> Task:
    updated = repo.update(task_id, payload)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea con id {task_id} no encontrada",
        )
    return updated


@app.patch("/tasks/{task_id}/complete", response_model=Task)
def complete_task(task_id: int) -> Task:
    updated = repo.mark_complete(task_id)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea con id {task_id} no encontrada",
        )
    return updated


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> None:
    if not repo.delete(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea con id {task_id} no encontrada",
        )
