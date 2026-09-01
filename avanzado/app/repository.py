import sqlite3
from datetime import UTC, date, datetime

import app.dates as dates
from app.database import get_connection
from app.list_params import OrdenCampo, OrdenDir, TaskListParams
from app.schemas import Prioridad, Task, TaskCreate, TaskUpdate


class TaskRepository:
    def _row_to_task(self, row: sqlite3.Row) -> Task:
        fecha_limite = (
            date.fromisoformat(row["fecha_limite"]) if row["fecha_limite"] else None
        )
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            completed=bool(row["completed"]),
            prioridad=Prioridad(row["prioridad"]),
            fecha_limite=fecha_limite,
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def create(self, payload: TaskCreate) -> Task:
        created_at = datetime.now(UTC).isoformat()
        data = payload.model_dump()
        fecha_limite = (
            data["fecha_limite"].isoformat() if data["fecha_limite"] is not None else None
        )

        conn = get_connection()
        try:
            cursor = conn.execute(
                """
                INSERT INTO tasks (
                    title, description, completed, created_at, prioridad, fecha_limite
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    data["title"],
                    data["description"],
                    int(data["completed"]),
                    created_at,
                    data["prioridad"].value,
                    fecha_limite,
                ),
            )
            conn.commit()
            task_id = cursor.lastrowid
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        finally:
            conn.close()

        return self._row_to_task(row)

    def list_all(self) -> list[Task]:
        return self.list_filtered(TaskListParams())

    def list_filtered(self, params: TaskListParams) -> list[Task]:
        where_clauses: list[str] = []
        query_params: list[object] = []

        if params.prioridad:
            placeholders = ", ".join("?" for _ in params.prioridad)
            where_clauses.append(f"prioridad IN ({placeholders})")
            query_params.extend(p.value for p in params.prioridad)

        if params.fecha_desde is not None:
            where_clauses.append("fecha_limite IS NOT NULL AND fecha_limite >= ?")
            query_params.append(params.fecha_desde.isoformat())

        if params.fecha_hasta is not None:
            where_clauses.append("fecha_limite IS NOT NULL AND fecha_limite <= ?")
            query_params.append(params.fecha_hasta.isoformat())

        if params.vencidas:
            where_clauses.append("completed = 0 AND fecha_limite IS NOT NULL AND fecha_limite < ?")
            query_params.append(dates.today_app().isoformat())

        if params.sin_fecha:
            where_clauses.append("fecha_limite IS NULL")

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        order_sql = self._build_order_clause(params)

        conn = get_connection()
        try:
            rows = conn.execute(
                f"SELECT * FROM tasks {where_sql} {order_sql}",
                query_params,
            ).fetchall()
        finally:
            conn.close()

        return [self._row_to_task(row) for row in rows]

    def _build_order_clause(self, params: TaskListParams) -> str:
        if params.orden == OrdenCampo.prioridad:
            direction = "ASC" if params.dir == OrdenDir.asc else "DESC"
            return (
                "ORDER BY CASE prioridad "
                "WHEN 'alta' THEN 3 WHEN 'media' THEN 2 WHEN 'baja' THEN 1 END "
                f"{direction}, fecha_limite IS NULL, fecha_limite ASC, id ASC"
            )

        if params.orden == OrdenCampo.fecha_limite:
            direction = "ASC" if params.dir == OrdenDir.asc else "DESC"
            return f"ORDER BY fecha_limite IS NULL, fecha_limite {direction}, id ASC"

        return (
            "ORDER BY CASE prioridad "
            "WHEN 'alta' THEN 3 WHEN 'media' THEN 2 WHEN 'baja' THEN 1 END DESC, "
            "fecha_limite IS NULL, fecha_limite ASC, id ASC"
        )

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

        conn = get_connection()
        try:
            conn.execute(
                "UPDATE tasks SET completed = 1 WHERE id = ?",
                (task_id,),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        finally:
            conn.close()

        return self._row_to_task(row)

    def delete(self, task_id: int) -> bool:
        conn = get_connection()
        try:
            cursor = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
