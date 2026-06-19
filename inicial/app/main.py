from fastapi import FastAPI, HTTPException, status

from app.schemas import Task, TaskCreate, TaskUpdate

app = FastAPI(title="CRUD de Tareas", version="1.0.0")

_tasks: dict[int, Task] = {}
_next_id = 1


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> Task:
    global _next_id
    task = Task(id=_next_id, **payload.model_dump())
    _tasks[_next_id] = task
    _next_id += 1
    return task


@app.get("/tasks", response_model=list[Task])
def list_tasks() -> list[Task]:
    return list(_tasks.values())


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, payload: TaskUpdate) -> Task:
    if task_id not in _tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea con id {task_id} no encontrada",
        )

    current = _tasks[task_id]
    updated = current.model_copy(update=payload.model_dump(exclude_unset=True))
    _tasks[task_id] = updated
    return updated


@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int) -> None:
    if task_id not in _tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tarea con id {task_id} no encontrada",
        )
    del _tasks[task_id]
