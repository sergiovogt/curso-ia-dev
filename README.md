# Curso: IA en el IDE para developers

Material de capacitación para equipos de desarrollo sobre cómo trabajar con
modelos de IA en el editor (Cursor y GitHub Copilot): cómo piensan los modelos,
cómo controlar el contexto y cómo usar las herramientas del IDE de forma efectiva.

El curso está organizado en tres niveles progresivos, cada uno con su proyecto
de práctica y su documentación.

## Estructura del repo

```
.
├── inicial/         # Nivel 1 — fundamentos + CRUD de práctica
│   ├── app/         # API de ejemplo (FastAPI) sobre la que se hacen las demos
│   ├── docs/        # Slides, cheatsheet y buenas prácticas
│   └── requirements.txt
├── intermedio/      # Nivel 2 — (en preparación)
└── avanzado/        # Nivel 3 — (en preparación)
```

## Nivel inicial

Proyecto de práctica: un **CRUD de tareas** en FastAPI, deliberadamente simple y
con "huecos" (sin tests, almacenamiento en memoria, endpoints faltantes) para
demostrar en vivo las funcionalidades del IDE: autocompletado, edición inline,
chat con contexto, reglas del proyecto y generación de tests.

### Requisitos

- Python 3.12+

### Puesta en marcha

```bash
cd inicial
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

La API queda disponible en `http://127.0.0.1:8000` y la documentación
interactiva en `http://127.0.0.1:8000/docs`.

### Documentación

En `inicial/docs/`:

- **`cheatsheet-cursor.md`** — comandos y atajos de Cursor en una hoja (Windows).
- **`buenas-practicas-tokens.md`** — optimización de contexto y tokens.
- **`Capacitacion_1_Slides.pptx`** — slides de la primera sesión.

## Niveles intermedio y avanzado

En preparación. Cubrirán prompts avanzados, reglas del proyecto, agent mode e
integración de la IA en el flujo de trabajo real.
