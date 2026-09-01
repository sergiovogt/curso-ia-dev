# Curso: IA aplicada para equipos de desarrollo

Material de capacitación sobre cómo trabajar con modelos de IA en el día a día
del desarrollo: cómo piensan los modelos, cómo controlar el contexto y los
tokens, y cómo llevar eso a un flujo de trabajo real.

Las sesiones se dictan con **Claude Code**, pero casi todo lo que se ve aplica
igual a cualquier agente de código —Codex, Gemini CLI o el que venga—, porque el
tema de fondo no es la herramienta sino cómo se le da contexto.

El curso está organizado en tres niveles progresivos, cada uno con su proyecto de
práctica sobre el **mismo CRUD de tareas en FastAPI**, que va ganando madurez a
medida que se sube de nivel.

## Estructura del repo

```
.
├── skills/          # Skills de ejemplo, entregadas con el nivel inicial
├── inicial/         # Nivel 1 — fundamentos: prompting, contexto y tokens
├── intermedio/      # Nivel 2 — skills de proyecto + MCP
└── avanzado/        # Nivel 3 — Spec-Driven Development (SDD)
```

Cada nivel es autocontenido: se trabaja parado dentro de su carpeta, con su
propio `requirements.txt`.

**Las diferencias entre los tres niveles son deliberadas.** Hay carencias puestas
a propósito —código sin tests, campos que no se exponen, endpoints que faltan—
que son el material de las sesiones. No las unifiquen ni las "arreglen" por
adelantado: son el ejercicio.

El stack es Python. Es a propósito que no coincida con el de tu equipo: lo que se
practica son las técnicas de trabajo con IA, no el framework.

### Requisitos

- Python 3.12+
- Un agente de código instalado (el curso usa Claude Code)

### Puesta en marcha

Idéntica en los tres niveles:

```bash
cd inicial            # o intermedio / avanzado
python -m venv .venv
# Windows:   .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API en `http://127.0.0.1:8000` y documentación interactiva en `/docs`.

---

## Nivel inicial — fundamentos

Un **CRUD de tareas** en FastAPI, deliberadamente simple. Es la base sobre la que
se practica lo esencial: escribir prompts específicos, entender qué ocupa la
ventana de contexto, y revisar lo que el agente propone antes de aceptarlo.

**Por dónde empezar:**

1. Clonar, entrar a `inicial/` y levantar el proyecto.
2. Abrir el agente parado en esa carpeta y correr `/context` **sin escribir
   nada**. Van a ver que una sesión vacía ya arranca con decenas de miles de
   tokens ocupados. Vale la pena mirar qué los ocupa.
3. Correr `/init` para que genere el archivo de contexto del proyecto, y después
   **leerlo entero**. Lo generado es un punto de partida, no el producto: casi
   siempre trae cosas de más y alguna interpretación equivocada, y ese archivo se
   carga en todas las sesiones siguientes.
4. Abrir el `settings.json` del usuario y el `.claude/settings.local.json` del
   proyecto, y leer qué permisos hay concedidos. Las reglas de `allow` le ganan
   al modo de permisos: si `Edit` está permitido, el diff de confirmación no
   aparece en ningún modo.

## Nivel intermedio — skills + MCP

El mismo CRUD, esta vez para practicar cómo **extender el agente**: dar contexto
a nivel de codebase con *skills* reutilizables, y a nivel de herramientas con
servidores *MCP*.

- Una skill de code review sobre el proyecto, con sus ejemplos.
- `docs/CODING_STANDARDS.md` — los estándares que la skill toma como referencia.
- `README-mcp.md` — cómo levantar y usar un MCP en este nivel.

## Nivel avanzado — Spec-Driven Development

El mismo CRUD, ahora con **página web** (server-rendered con Jinja2) y sembrado
con tareas de ejemplo. Es la base para practicar el flujo **spec → plan →
tasks**: en vez de pedirle al agente que construya algo directo, se define
primero *qué* hay que construir y *qué significa que está terminado*, con
revisión humana en cada paso.

- `templates/spec.md`, `plan.md`, `tasks.md` — esqueletos reutilizables de los
  tres artefactos. Se copian y se completan para cada feature nueva.

Este nivel arranca **sin la feature construida**: el punto de partida es común, y
durante la sesión se construye la misma funcionalidad de dos maneras distintas
para poder compararlas. Las ramas con cada versión se publican en su momento.

---

## Skills

En `skills/` hay dos skills de ejemplo que se entregan con el nivel inicial:
`log-session` y `retomar-sesion`. Resuelven qué hacer cuando el contexto se
llena — registrar la sesión, limpiarla y retomarla sin arrastrar el ruido.

Ver **[`skills/README.md`](skills/README.md)** para la instalación y para cómo
está hecha una skill por dentro.
