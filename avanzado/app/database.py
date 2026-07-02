import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "tasks.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    _seed_if_empty(conn)
    conn.close()


# Tareas de arranque para la demo de SDD (cap-5). Existen a propósito ANTES de
# agregar prioridad y fecha límite: son los datos "viejos" que la migración de
# la feature tiene que contemplar. Fechas fijas para que la demo sea reproducible.
_SEED_TASKS = [
    ("Configurar el pipeline de CI", "Correr tests en cada push a main", 1, "2026-06-02T09:15:00+00:00"),
    ("Migrar el login a OAuth", "Reemplazar el login por usuario/clave", 0, "2026-06-05T14:30:00+00:00"),
    ("Escribir la doc del endpoint de pagos", None, 0, "2026-06-09T11:00:00+00:00"),
    ("Revisar el PR de checkout", "Quedó pendiente de cap-3", 0, "2026-06-12T16:45:00+00:00"),
    ("Actualizar dependencias de FastAPI", "Subir a la última menor", 1, "2026-06-16T08:20:00+00:00"),
]


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    """Siembra tareas de ejemplo solo si la tabla está vacía.

    Idempotente: al reiniciar sobre una base ya sembrada no duplica nada. Para
    volver al estado inicial de la demo, borrar tasks.db y reiniciar la app.
    """
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count > 0:
        return
    conn.executemany(
        """
        INSERT INTO tasks (title, description, completed, created_at)
        VALUES (?, ?, ?, ?)
        """,
        _SEED_TASKS,
    )
    conn.commit()
