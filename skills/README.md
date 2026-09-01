# Skills

Dos skills de ejemplo, entregadas con el **módulo 1**. Resuelven un problema
concreto que apareció en la sesión: **qué hacer cuando el contexto se llena.**

## El problema

Una sesión larga con un agente termina llena de material que ya no sirve:
archivos que se leyeron una vez, caminos que no llevaron a nada, respuestas
descartadas. Cuando la ventana se acerca al límite, la calidad cae — y si
simplemente hacés `/clear`, perdés todo lo que decidiste y por qué.

## El ciclo

```
[trabajás hasta ~70-80% de la ventana]
        │
        ├─ /log-session      vuelca lo trabajado a una nota del vault
        │                    (qué se decidió, por qué, qué quedó abierto)
        │
        ├─ /clear            limpia la sesión: contexto en cero
        │
        └─ /retomar-sesion   lee la nota y reconstruye el contexto,
                             sin el ruido de la sesión anterior
```

La idea de fondo: **el contexto no vive en la conversación, vive en un lugar
propio del que se recupera cuando hace falta.** La conversación es descartable;
la base de conocimiento no.

## Las dos skills

| Skill | Qué hace |
|---|---|
| **`log-session`** | Escribe un registro estructurado de la sesión en `<vault>/Sesiones/YYYY-MM-DD.md`: qué se investigó, qué se decidió y por qué, archivos tocados, gotchas y pendientes. Enlaza la nota al overview del proyecto en las dos direcciones, para que no quede huérfana del grafo. Escribe. |
| **`retomar-sesion`** | Lee el último registro y devuelve un briefing corto: qué se trabajó, qué cerró, qué quedó abierto y desde cuándo se viene arrastrando. Solo lectura. |

Son el espejo una de la otra: la primera escribe el formato que la segunda sabe
leer. Si cambiás una, mirá la otra.

## Instalación

Las skills se pueden instalar en dos alcances:

| Alcance | Dónde | Cuándo |
|---|---|---|
| **Usuario** | `~/.claude/skills/` | Disponibles en todos tus proyectos |
| **Proyecto** | `.claude/skills/` del repo | Solo dentro de ese repo, y viajan con él |

**Estas dos van a alcance de usuario**, porque el registro de sesiones es algo
que vas a querer en todos tus proyectos, no solo en este:

```bash
cp -r skills/log-session   ~/.claude/skills/
cp -r skills/retomar-sesion ~/.claude/skills/
```

En Windows, `~` es `C:\Users\<usuario>\`. Quedaría así:

```
~/.claude/skills/
├── log-session/
│   └── SKILL.md
└── retomar-sesion/
    └── SKILL.md
```

Se invocan con `/log-session` y `/retomar-sesion`.

## Cómo adaptarlas

Vienen con las convenciones de quien las escribió. Tres cosas a revisar:

1. **La ruta del vault.** Aparece como `<ruta-a-tu-vault>`. Lo más cómodo es
   dejar la ruta en el `CLAUDE.md` del repo: es lo primero que las skills
   buscan, y así cada proyecto escribe en su carpeta sin tocar la skill.

2. **La estructura de carpetas.** Asumen `Sesiones/` para los registros y un
   `00-overview.md` por proyecto. Si usás otra convención, cambiala en el
   `SKILL.md`.

3. **El formato del registro.** El bloque *"Formato de las notas"* de
   `log-session` define las secciones: `Contexto / Síntoma`,
   `Causa raíz / Decisiones de diseño`, `Archivos modificados`,
   `Notas técnicas`, `Pendiente`. Ajustalo a lo que a vos te sirva leer tres
   semanas después. Si tocás esto, revisá también cómo lee `retomar-sesion`,
   sobre todo el bloque `### Pendiente`.

## Cómo está hecha una skill

Abrí cualquiera de los dos `SKILL.md`: no hay magia. Es un archivo Markdown con
un frontmatter de dos campos y, abajo, instrucciones en prosa.

```markdown
---
name: log-session
description: Registra lo trabajado en la sesión actual en el vault de Obsidian
             del proyecto activo. Usar cuando el usuario pide guardar, registrar
             o anotar la sesión en Obsidian.
---

# Skill: log-session
...
```

El `description` es lo que decide **cuándo** se activa la skill, así que conviene
que diga explícitamente en qué situaciones usarla. El cuerpo es lo que el agente
lee cuando se activa.

Fijate que las dos tienen bastante espacio dedicado a **qué no hacer**:
`retomar-sesion` tiene una tabla entera de errores comunes, y `log-session`
aclara que nunca hay que transcribir el diálogo. Eso no es relleno — es la parte
que evita que el resultado salga mal, y suele ser lo que más se olvida al
escribir una skill.

Una skill no es otra cosa que **conocimiento congelado**: un prompt que ya
afinaste, con nombre, para no volver a reconstruirlo cada vez.

En el **módulo 2** las vemos en profundidad y cada uno escribe la suya.
