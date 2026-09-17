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
            priority TEXT NOT NULL DEFAULT 'media',
            due_date TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    _add_missing_columns(conn)
    conn.commit()
    _seed_if_empty(conn)
    conn.close()


def _add_missing_columns(conn: sqlite3.Connection) -> None:
    """Agrega prioridad y fecha límite a una base creada antes de que existieran."""
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
    if "priority" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN priority TEXT NOT NULL DEFAULT 'media'")
    if "due_date" not in columns:
        conn.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")


# Tareas de ejemplo. Fechas fijas para que el estado inicial sea reproducible.
_SEED_TASKS = [
    ("Configurar el pipeline de CI", "Correr tests en cada push a main", 1, "alta", "2026-06-10", "2026-06-02T09:15:00+00:00"),
    ("Migrar el login a OAuth", "Reemplazar el login por usuario/clave", 0, "alta", "2026-07-01", "2026-06-05T14:30:00+00:00"),
    ("Escribir la doc del endpoint de pagos", None, 0, "baja", None, "2026-06-09T11:00:00+00:00"),
    ("Revisar el PR de checkout", "Quedó pendiente de cap-3", 0, "media", "2026-12-15", "2026-06-12T16:45:00+00:00"),
    ("Actualizar dependencias de FastAPI", "Subir a la última menor", 1, "baja", None, "2026-06-16T08:20:00+00:00"),
]


def _seed_if_empty(conn: sqlite3.Connection) -> None:
    """Siembra tareas de ejemplo solo si la tabla está vacía.

    Idempotente: al reiniciar sobre una base ya sembrada no duplica nada. Para
    volver al estado inicial, borrar tasks.db y reiniciar la app.
    """
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count > 0:
        return
    conn.executemany(
        """
        INSERT INTO tasks (title, description, completed, priority, due_date, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        _SEED_TASKS,
    )
    conn.commit()
