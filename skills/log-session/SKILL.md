---
name: log-session
description: Registra lo trabajado en la sesión actual en el vault de Obsidian del proyecto activo. Usar cuando el usuario pide guardar, registrar o anotar la sesión en Obsidian.
---

# Skill: log-session

Guardá un registro de la sesión actual en el vault de Obsidian del proyecto activo.

## Cómo determinar la ruta de Obsidian

1. Leé el `CLAUDE.md` del directorio de trabajo actual.
2. Buscá la sección "Obsidian notes" (o similar) que indique la ruta del vault del proyecto.
3. Usá esa ruta como carpeta base y appendeá `/Sesiones/YYYY-MM-DD.md`.
4. Si el `CLAUDE.md` no indica ruta, pero el directorio de trabajo **está adentro del vault**, usá ese directorio como carpeta base.
5. Si ninguna de las dos aplica, **preguntale al usuario dónde guardar la sesión**. No adivines: escribir el log en el proyecto equivocado es peor que no escribirlo.

> Las rutas en `CLAUDE.md` están en formato Windows (`C:\...`). Convertí a WSL (`/mnt/c/...`) y reemplazá `\` por `/` antes de usarlas.

La fecha del archivo es la de la sesión. Si el usuario no especifica fecha, **usá siempre la fecha de hoy en UTC-3 (zona horaria de Argentina)**, sin importar la zona horaria del sistema. No uses la fecha del sistema directamente: obtené la fecha en UTC-3 con

```bash
TZ="America/Argentina/Buenos_Aires" date +%Y-%m-%d
```

## Comportamiento

1. **Determiná la ruta** siguiendo los pasos anteriores.
2. **Verificá si el archivo ya existe** con Read.
   - Si existe: **appendeá** una nueva sección al final (no sobreescribas). No repitas los pasos de conexión (ya está enlazado).
   - Si no existe: **crealo** con el encabezado `# Sesión YYYY-MM-DD` seguido del **up-link al overview** (ver "Conexión al overview").
3. **Analizá la conversación** para extraer lo trabajado. No describas el diálogo — describí el trabajo técnico: qué se investigó, qué se diseñó, qué se implementó, qué se debugueó.
4. **Escribí el contenido** siguiendo el formato establecido (ver abajo).
5. **Conectá la sesión al overview** (solo si el archivo es nuevo) siguiendo "Conexión al overview".
6. Confirmá al usuario con una línea: ruta del archivo, si fue creado o actualizado, y si se enlazó al overview.

---

## Conexión al overview

Cada sesión nueva debe quedar conectada en **las dos direcciones**: la sesión apunta al overview (up-link) y el overview lista la sesión. Esto evita que las sesiones queden huérfanas del grafo de Obsidian.

### Paso 0: ubicar el overview

La sesión vive en `<base>/Sesiones/YYYY-MM-DD.md`. El overview del proyecto es `<base>/00-overview.md`.

- Verificá que `<base>/00-overview.md` exista con Read.
- Si **no existe**, omití los dos pasos de conexión y avisale al usuario que no encontró overview en ese proyecto (no inventes uno).

Necesitás la **ruta relativa al vault** del overview (sin el prefijo `<ruta-a-tu-vault>/`). Ej: `Proyectos/<Proyecto>/00-overview.md`.

### Paso 1: up-link en la sesión

Justo debajo del `# Sesión YYYY-MM-DD`, agregá una línea con la ruta **completa del vault** (no uses `[[00-overview]]` pelado — hay muchos overviews y el link quedaría ambiguo):

```markdown
# Sesión YYYY-MM-DD

> Sesión de [[<ruta-vault-del-overview>|<Nombre del proyecto>]]
```

### Paso 2: listar la sesión en el overview

Editá el overview para agregar el link a la sesión:

- Buscá la sección de sesiones (encabezado que empiece con `## Sesiones`, p. ej. `## Sesiones de trabajo`).
- Agregá un ítem **en orden cronológico** (las fechas más nuevas al final de la lista, salvo que la lista existente esté en orden inverso — respetá el orden que ya tenga):
  ```markdown
  - [[Sesiones/YYYY-MM-DD.md|YYYY-MM-DD]]
  ```
- Si la lista de sesiones está anidada bajo un bullet (como en algunos overviews), agregá el ítem como sub-bullet manteniendo la indentación.
- Si **no existe** ninguna sección de sesiones, creá una al final del overview:
  ```markdown
  ## Sesiones de trabajo

  - [[Sesiones/YYYY-MM-DD.md|YYYY-MM-DD]]
  ```

---

## Formato de las notas

Cada bloque de trabajo es una sección `## Parte N: <título>`. Si el archivo ya tenía partes, numerá desde donde quedó.

### Estructura por parte

```markdown
## Parte N: <título descriptivo>

### Contexto / Síntoma
Qué disparó este trabajo. Si es un bug: síntoma observado.

### Causa raíz / Decisiones de diseño
Explicación técnica de lo encontrado o decidido. Tablas para decisiones múltiples:

| Pregunta | Decisión |
|----------|----------|
| ...      | ...      |

### Archivos modificados

**Backend / Frontend / Infra** (según aplique):

| Archivo | Cambio |
|---------|--------|
| `ruta/archivo.py` | Qué se modificó y por qué |

### Notas técnicas
Cualquier detalle no obvio: trampas, comportamientos inesperados de APIs externas,
workarounds, gotchas. Priorizá lo que sorprendería a alguien leyendo el código.

### Pendiente
Lista de tareas que quedaron abiertas. Tachar con ~~texto~~ ✅ las completadas.
Omitir sección si no hay pendientes.
```

---

## Convenciones de formato

- Bloques de código para comandos, IDs, payloads de API.
- Tablas para listas de archivos modificados y decisiones de diseño.
- Negrita para causas raíz y conceptos clave.
- Nunca transcribir el diálogo de la conversación.
- Si algo de la API externa resultó diferente a lo documentado (campos distintos, estructura anidada, valores distintos), documentarlo explícitamente — es lo más valioso para reutilizar.

---

## Qué incluir siempre (si aplica)

- Respuestas reales de APIs externas que difirieron de lo esperado
- Errores de migración / configuración y su solución
- Workarounds de entorno (Docker, WSL2, puertos, etc.)
- Decisiones de diseño con su justificación
- Comandos concretos para reproducir o revertir algo
