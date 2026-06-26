# Convenciones de Code Review — API FastAPI (intermedio)

## Arquitectura
- Las rutas no acceden directamente a repositorios globales.
- Usar inyección de dependencias con `Depends()` para obtener el repositorio o servicio.
- Estructura preferida: router → servicio (opcional) → repositorio.

## Organización de la API
- Agrupar endpoints con `APIRouter` y prefijo `/tasks`.
- Añadir `tags=["tasks"]` para documentación OpenAPI.
- Exponer `GET /health` con respuesta mínima `{"status": "ok"}`.

## Manejo de errores
- No repetir bloques `HTTPException` idénticos; extraer helper o dependencia reutilizable.
- Mensajes de error en español, centralizados (no strings sueltos en cada endpoint).
- Recursos no encontrados: siempre `404` con mensaje `"Tarea con id {id} no encontrada"`.

## Validación y contratos
- Path params numéricos de ID deben validarse con `Path(..., ge=1)`.
- Listados deben soportar paginación (`limit`, `offset`) con valores por defecto razonables.

## Estilo Python / FastAPI
- Type hints obligatorios en parámetros y retorno.
- Docstrings breves en cada endpoint (qué hace + código HTTP).
- Preferir funciones pequeñas; si un handler supera ~10 líneas, extraer lógica.

## Respuestas HTTP
- `POST` crea → `201`; `DELETE` exitoso → `204` sin body.
- Usar `status.HTTP_*` en lugar de números mágicos (ya aplicado; mantener).
