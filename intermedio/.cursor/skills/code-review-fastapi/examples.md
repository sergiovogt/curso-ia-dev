# Ejemplo de reporte — main.py

Contexto: revisión de `intermedio/app/main.py` antes de aplicar mejoras.

---

## Qué cumple
- Type hints en parámetros y retorno de todos los handlers.
- `POST /tasks` responde `201`; `DELETE /tasks/{task_id}` responde `204`.
- Uso de `status.HTTP_*` en lugar de números mágicos.
- Mensajes 404 en español con formato `"Tarea con id {task_id} no encontrada"`.
- Handlers cortos; delegación al repositorio sin SQL en la capa HTTP.

## Incumplimientos

| Severidad | Regla incumplida | Ubicación | Mejora sugerida |
|-----------|-----------------|-----------|-----------------|
| Alta | Repositorio global sin `Depends()` | L9 | Crear `get_task_repository()` e inyectar con `Depends()`. |
| Alta | Endpoints sin `APIRouter` | L21–70 | Mover a router con `prefix="/tasks"` e `include_router`. |
| Alta | Falta `GET /health` | — | Añadir endpoint que devuelva `{"status": "ok"}`. |
| Media | Bloques `HTTPException` repetidos | L34–38, L45–49, L56–60, L66–70 | Extraer helper `raise_task_not_found(task_id)`. |
| Media | Mensajes no centralizados | L37, L48, L59, L69 | Constante o módulo `errors.py` con el mensaje. |
| Media | `task_id` sin `Path(..., ge=1)` | L32, L43, L54, L65 | Usar `Annotated[int, Path(..., ge=1)]`. |
| Media | Listado sin paginación | L26–28 | Añadir `limit`/`offset` con defaults y soporte en repo. |
| Baja | Sin docstrings en endpoints | L21–70 | Docstring breve por handler (acción + HTTP). |
| Baja | Sin `tags=["tasks"]` | L21–70 | Configurar tags al migrar a `APIRouter`. |
