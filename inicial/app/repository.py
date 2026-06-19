import sqlite3
from datetime import UTC, datetime

from app.database import get_connection
from app.schemas import Task, TaskCreate, TaskUpdate


class TaskRepository:
    def _row_to_task(self, row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            completed=bool(row["completed"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            priority=row["priority"],
        )

    def create(self, payload: TaskCreate) -> Task:
        created_at = datetime.now(UTC).isoformat()
        data = payload.model_dump()

        conn = get_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO tasks (title, description, completed, created_at, priority)
                VALUES (?, ?, ?, ?, 0)
                """,
                (data["title"], data["description"], int(data["completed"]), created_at),
            )
            conn.commit()
            task_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        finally:
            conn.close()

        return self._row_to_task(row)

    def list_all(self) -> list[Task]:
        conn = get_connection()
        try:
            rows = conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()
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
                SET title = ?, description = ?, completed = ?
                WHERE id = ?
                """,
                (
                    updated.title,
                    updated.description,
                    int(updated.completed),
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
