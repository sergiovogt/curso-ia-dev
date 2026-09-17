import sqlite3
from datetime import UTC, date, datetime

from app.database import get_connection
from app.schemas import Priority, Task, TaskCreate, TaskFilters, TaskUpdate


def _date_to_text(value: date | None) -> str | None:
    return value.isoformat() if value is not None else None


class TaskRepository:
    def _row_to_task(self, row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            completed=bool(row["completed"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            priority=Priority(row["priority"]),
            due_date=date.fromisoformat(row["due_date"]) if row["due_date"] else None,
        )

    def create(self, payload: TaskCreate) -> Task:
        created_at = datetime.now(UTC).isoformat()
        data = payload.model_dump()

        conn = get_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO tasks (title, description, completed, created_at, priority, due_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    data["title"],
                    data["description"],
                    int(data["completed"]),
                    created_at,
                    data["priority"].value,
                    _date_to_text(data["due_date"]),
                ),
            )
            conn.commit()
            task_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        finally:
            conn.close()

        return self._row_to_task(row)

    def list_all(self, filters: TaskFilters | None = None) -> list[Task]:
        filters = filters or TaskFilters()
        clauses: list[str] = []
        params: list[str | int] = []
        if filters.priority is not None:
            clauses.append("priority = ?")
            params.append(filters.priority.value)
        if filters.completed is not None:
            clauses.append("completed = ?")
            params.append(int(filters.completed))
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

        conn = get_connection()
        try:
            rows = conn.execute(f"SELECT * FROM tasks {where} ORDER BY id", params).fetchall()
        finally:
            conn.close()

        return [self._row_to_task(row) for row in rows]

    def get_by_id(self, task_id: int) -> Task | None:
        conn = get_connection()
        try:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        finally:
            conn.close()

        if row is None:
            return None
        return self._row_to_task(row)

    def update(self, task_id: int, payload: TaskUpdate) -> Task | None:
        current = self.get_by_id(task_id)
        if current is None:
            return None

        updated = current.model_copy(update=payload.model_dump(exclude_unset=True))

        conn = get_connection()
        try:
            conn.execute(
                """
                UPDATE tasks
                SET title = ?, description = ?, completed = ?, priority = ?, due_date = ?
                WHERE id = ?
                """,
                (
                    updated.title,
                    updated.description,
                    int(updated.completed),
                    updated.priority.value,
                    _date_to_text(updated.due_date),
                    task_id,
                ),
            )
            conn.commit()
        finally:
            conn.close()

        return updated

    def mark_complete(self, task_id: int) -> Task | None:
        current = self.get_by_id(task_id)
        if current is None:
            return None

        updated = current.model_copy(update={"completed": True})

        conn = get_connection()
        try:
            conn.execute(
                "UPDATE tasks SET completed = 1 WHERE id = ?",
                (task_id,),
            )
            conn.commit()
        finally:
            conn.close()

        return updated

    def delete(self, task_id: int) -> bool:
        conn = get_connection()
        try:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
