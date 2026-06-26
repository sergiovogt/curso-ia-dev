from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status

from app.database import init_db
from app.repository import TaskRepository
from app.schemas import Task, TaskCreate, TaskUpdate

repo = TaskRepository()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="CRUD de Tareas", version="1.0.0", lifespan=lifespan)


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
