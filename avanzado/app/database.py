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
    _migrate(conn)
    _seed_if_empty(conn)
    conn.close()


# Columnas agregadas después del esquema original, con su definición. Una base
# vieja las recibe al arrancar; las filas existentes toman el DEFAULT.
_ADDED_COLUMNS = {
    "priority": "TEXT NOT NULL DEFAULT 'media'",
    "due_date": "TEXT",
}


def _migrate(conn: sqlite3.Connection) -> None:
    """Agrega a la tabla tasks las columnas que le falten.

    Idempotente: mira qué columnas ya existen, así que correrla sobre una base
    ya migrada no hace nada. Cada columna se agrega por separado para que una
    migración cortada a la mitad se complete en el próximo arranque.
    """
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(tasks)")}
    for name, definition in _ADDED_COLUMNS.items():
        if name not in existing:
            conn.execute(f"ALTER TABLE tasks ADD COLUMN {name} {definition}")
    conn.commit()


# Tareas de ejemplo. Fechas fijas para que el estado inicial sea reproducible.
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
    volver al estado inicial, borrar tasks.db y reiniciar la app.
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
