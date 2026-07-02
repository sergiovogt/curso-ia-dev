from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import init_db
from app.repository import TaskRepository
from app.schemas import Task, TaskCreate, TaskUpdate

repo = TaskRepository()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent / "templates")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="CRUD de Tareas", version="1.0.0", lifespan=lifespan)


# --- UI (páginas server-rendered) ---


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    tasks = repo.list_all()
    return templates.TemplateResponse(request, "index.html", {"tasks": tasks})


@app.post("/ui/tasks")
def ui_create_task(title: str = Form(...), description: str = Form("")) -> RedirectResponse:
    repo.create(TaskCreate(title=title, description=description or None))
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
def list_tasks() -> list[Task]:
    return repo.list_all()


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
