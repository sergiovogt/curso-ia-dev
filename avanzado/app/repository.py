import sqlite3
from datetime import UTC, date, datetime, timedelta

from app.database import get_connection
from app.schemas import Priority, Task, TaskCreate, TaskUpdate


# Claves de orden permitidas -> cláusula ORDER BY. Nunca se interpola el valor del usuario.
_ORDER_BY: dict[str, str] = {
    "prioridad": "CASE priority WHEN 'alta' THEN 0 WHEN 'media' THEN 1 ELSE 2 END, due_date IS NULL, due_date, id",
    "fecha_limite": "due_date IS NULL, due_date, id",
}


class TaskRepository:
    def _row_to_task(self, row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            completed=bool(row["completed"]),
            priority=Priority(row["priority"]),
            due_date=date.fromisoformat(row["due_date"]) if row["due_date"] else None,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def create(self, payload: TaskCreate) -> Task:
        created_at = datetime.now(UTC).isoformat()
        data = payload.model_dump()

        conn = get_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO tasks (title, description, completed, priority, due_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    data["title"],
                    data["description"],
                    int(data["completed"]),
                    data["priority"].value,
                    data["due_date"].isoformat() if data["due_date"] else None,
                    created_at,
                ),
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

    def list_filtered(
        self,
        priority: Priority | None = None,
        due: str | None = None,
        sort: str | None = None,
        today: date | None = None,
    ) -> list[Task]:
        """Lista tareas filtradas por prioridad y vencimiento, en el orden pedido.

        `due`: "vencidas" (fecha límite pasada y sin completar), "proximas" (vencen
        entre hoy y 7 días) o "sin_fecha". `sort`: "prioridad" o "fecha_limite";
        cualquier otro valor ordena por creación.
        """
        today = today or date.today()
        conditions: list[str] = []
        params: list[str] = []

        if priority is not None:
            conditions.append("priority = ?")
            params.append(priority.value)
        if due == "vencidas":
            conditions.append("due_date < ? AND completed = 0")
            params.append(today.isoformat())
        elif due == "proximas":
            conditions.append("due_date BETWEEN ? AND ?")
            params.extend([today.isoformat(), (today + timedelta(days=7)).isoformat()])
        elif due == "sin_fecha":
            conditions.append("due_date IS NULL")

        order_by = _ORDER_BY.get(sort or "", "id")
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        conn = get_connection()
        try:
            rows = conn.execute(f"SELECT * FROM tasks {where} ORDER BY {order_by}", params).fetchall()
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
                    updated.due_date.isoformat() if updated.due_date else None,
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
