# Cheatsheet Cursor — Windows

> Una hoja con lo esencial. Atajos para **Windows** (`Ctrl` / `Alt`).

---

## ⌨️ Atajos esenciales

| Atajo | Qué hace |
|---|---|
| `Ctrl + L` | Abrir **Chat** (panel lateral) — conversación, multi-archivo |
| `Ctrl + K` | **Inline edit** — editar el código seleccionado ahí mismo |
| `Ctrl + I` | **Composer / Agent** — cambios en varios archivos a la vez |
| `Tab` | Aceptar la sugerencia de **autocomplete** |
| `Esc` | Rechazar / cerrar la sugerencia |
| `Ctrl + →` | Aceptar la sugerencia **palabra por palabra** |
| `Ctrl + N` (en chat) | **Chat nuevo** — limpiar contexto al cambiar de tarea |
| `Ctrl + Enter` | Enviar el prompt (en Chat / K) |
| `Ctrl + Shift + L` | Agregar la selección actual al chat |
| `Ctrl + Shift + P` | Paleta de comandos (igual que VS Code) |
| `Ctrl + Shift + I` | Aceptar todos los cambios del diff |

> En **inline edit** y **Composer**: el resultado aparece como **diff**. Revisás y **Aceptás / Rechazás** — nunca se aplica solo.

---

## 🎯 Controlar el contexto con `@`

El modelo **NO lee todo el proyecto solo**. Vos le decís qué mirar:

| Símbolo | Para qué |
|---|---|
| `@archivo.py` | Incluir un archivo específico (lo más usado y preciso) |
| `@carpeta/` | Incluir una carpeta |
| `@Codebase` | Buscar en todo el proyecto indexado (usar con criterio: es caro y ruidoso) |
| `@Docs` | Documentación de librerías |
| `@Browser` | Buscar / traer contenido de internet |
| `@Branch` | Diffs y commits recientes |

**Regla:** si conocés los archivos del problema, nombralos explícitos con `@archivo`. Evitá `@Codebase` para tareas puntuales.

---

## 🛠️ Las 3 herramientas — cuándo usar cada una

| Herramienta | Atajo | Para |
|---|---|---|
| **Tab** (autocomplete) | `Tab` | Completar líneas/bloques mientras escribís. Siempre activo. |
| **Inline edit** | `Ctrl + K` | Cambio localizado en una función/selección. Rápido. |
| **Chat** | `Ctrl + L` | Preguntar, explicar, debuggear, tocar varios archivos. |
| **Composer / Agent** | `Ctrl + I` | Tareas grandes multi-archivo. Pedí **plan primero**. |

---

## ✍️ Anatomía de un buen prompt

1. **Qué** querés cambiar → específico, no vago
2. **Por qué / contexto** → el problema que resolvés
3. **Qué NO tocar** → límites claros
4. **Formato** esperado → si importa, decilo

> **Regla de oro:** si el prompt lo podría haber escrito alguien que no conoce el código, es demasiado vago. Dale el mismo contexto que a un dev nuevo.

**Malo:** `arreglá el bug`
**Bueno:** `En processPayment(), cuando el request hace timeout el error se traga silencioso. Lanzá un Error con mensaje "Payment timeout". No toques el manejo de los otros errores.`

---

## 🧠 Elegir modelo (selector del chat)

| Tipo | Para | Costo/velocidad |
|---|---|---|
| **Razonamiento** (Sonnet, Gemini Pro) | Arquitectura, debugging complejo, razonar sobre el sistema | Más lento / más caro |
| **Rápido** (Haiku, Gemini Flash) | Autocompletar, preguntas simples, transformaciones mecánicas | Más rápido / más barato |

> Los nombres exactos cambian seguido — mirá el **selector real** en el panel de chat.

---

## ⚙️ Configuración clave

- **`.cursorrules`** (raíz del proyecto): reglas fijas del repo (stack, convenciones, estilo). Se aplican **siempre**, sin repetirlas en cada prompt.
- **`.gitignore`**: Cursor hereda las exclusiones. Mantené fuera `dist/`, `node_modules/`, `.venv/`, logs, binarios → el indexador no mete ruido.
- **Privacy Mode** (Settings): el código **no se almacena** en servidores de Cursor. Activable por proyecto o global.

---

## ⚠️ 5 errores comunes

1. **Aceptar sin leer** — el modelo se equivoca con confianza. Vos sos responsable.
2. **Prompts vagos** — "mejorá el código" no dice nada.
3. **Todo en un prompt** — un prompt, un resultado. Pasos chicos.
4. **Frustrarse a la primera** — hay curva; mejora con práctica.
5. **Llenar el contexto sin pensar** — más irrelevante = peor respuesta. Chat nuevo (`Ctrl+N`) al cambiar de tarea.

---

> 💡 **Mantra:** *"¿Le di el contexto justo? ¿Revisé el diff antes de aceptar?"*
