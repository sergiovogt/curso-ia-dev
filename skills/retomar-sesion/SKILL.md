---
name: retomar-sesion
description: Usar cuando el usuario quiere ponerse en contexto de lo trabajado, retomar el trabajo de un proyecto, o arranca un chat limpio sobre un proyecto que ya tiene registros de sesión en el vault de Obsidian.
---

# Skill: retomar-sesion

Espejo de lectura de `log-session`. Recolecta el último registro de sesión del proyecto activo y devuelve un briefing corto. **No escribe ningún archivo.**

## Cómo determinar la ruta

Idéntica a `log-session`:

1. Leé el `CLAUDE.md` del directorio de trabajo actual y buscá la sección que indique la ruta del vault del proyecto.
2. Si no la indica pero el directorio de trabajo **está adentro del vault**, usá ese directorio como carpeta base.
3. Si ninguna aplica, **preguntale al usuario**. No adivines: cargar el contexto del proyecto equivocado es peor que no cargar ninguno.

> Rutas en formato Windows (`C:\...`) → convertir a WSL (`/mnt/c/...`) y `\` → `/`.

Carpeta a leer: `<base>/Sesiones/`.

## Comportamiento

1. **Fecha de hoy en UTC-3**, no la del sistema, para calcular la antigüedad del registro:
   ```bash
   TZ="America/Argentina/Buenos_Aires" date +%Y-%m-%d
   ```

2. **Listar los 4 registros más recientes**:
   ```bash
   ls -1 "<base>/Sesiones/"*.md | sort | tail -4
   ```
   Si la carpeta no existe o está vacía, decilo y pará. No inventes contexto.

3. **Leer entero el último** (el de `tail -1`) con Read.

4. **De los 3 anteriores, extraer solo los bloques `### Pendiente`** — no los leas enteros:
   ```bash
   awk '/^### Pendiente/{f=1;next} /^#{2,4} /{f=0} f' <archivo>
   ```

5. **Emitir el briefing** con el formato de abajo. Ahí termina la skill: no propongas trabajo ni arranques tareas hasta que el usuario diga qué quiere hacer.

## Reglas de lectura de pendientes

Las tres salen del formato real que escribe `log-session`:

- **Un archivo tiene varios `### Pendiente`**, uno por `## Parte N`, y se **unen todos** — no alcanza con el último. Un bloque puede ser un cierre que re-lista lo de las partes anteriores, o puede ser acotado a su propia parte; una parte agregada más tarde en el día no anula el "Estado al cierre" de una anterior.
- **Al unir, deduplicá por tema** y quedate con la redacción del bloque más nuevo: los cierres suelen repetir un ítem ya listado ("ABC-123 sigue sin spec").
- **Los tachados no van.** `~~texto~~ ✅` significa cerrado. Si un tema aparece pelado en un bloque y tachado en otro posterior, **gana el tachado**: se descarta.
- **El último archivo ya arrastra**, porque el cierre re-lista lo que sigue abierto de días previos. Por eso los archivos anteriores **no** aportan pendientes propios al briefing, sin excepción: **lo que dejó de re-listarse está resuelto**. No lo reportes, no lo marques para revisar, no pidas un doble check. El único pendiente es lo que el último archivo lista sin tachar.
- **Un pendiente que se ejecuta en otro repo no va al briefing.** Los registros anotan pasos manuales de tickets de clientes o de otros productos ("al mergear ABC-123, tocar el `.env` de tal repo"). Ese trabajo no se hace acá: **descartalo**, ni en `## Abierto` ni en una sección aparte.
- **Los 2 archivos más viejos sirven para fechar**, no para sumar ítems: si un pendiente del último ya figuraba ahí, decí desde cuándo viene arrastrándose (`ABC-123, abierto desde 2026-08-08`). Es la señal de qué se está postergando.

## Formato del briefing

```markdown
# 🔄 Retomando — {Proyecto}

> Última sesión: [[Sesiones/YYYY-MM-DD.md|YYYY-MM-DD]] ({hoy | ayer | hace N días})

## Qué se trabajó
- {un bullet por `## Parte N`, concreto y en pasado}

## Cerrado
{lo mergeado / desplegado / pasado a Listo. Omitir la sección si no hay.}

## Abierto
- {pendiente no tachado del último archivo} {— *abierto desde YYYY-MM-DD* si ya venía de antes}

## Dónde se retoma
{1-3 líneas: el punto exacto donde quedó el trabajo y qué sigue, según lo anotado}
```

## Reglas duras

- **No inventar.** Todo el briefing sale de los archivos leídos. Si algo no está anotado, escribir "no anotado" en vez de rellenar.
- **No escribir archivos.** Es de solo lectura — el que escribe es `log-session`.
- **No arrancar trabajo.** El briefing es el entregable completo.
- Español rioplatense, registro profesional, sin relleno ni arenga.

## Errores comunes

| Error | Qué pasa |
|---|---|
| Leer enteros los 4 archivos | 100+ KB de contexto al pedo; solo el último se lee entero |
| Reportar pendientes tachados | Devolvés como abierto algo que se cerró hace días |
| Quedarte con un solo `### Pendiente` del archivo | Perdés partes enteras: ni el primero ni el último cubren solos el día |
| Concatenar el arrastre sin filtrar | El mismo pendiente aparece 3 veces porque el cierre ya lo re-lista |
| Asumir que el último archivo es de ayer | Puede haber huecos de días; calculá la antigüedad y decila |
| Resucitar un ítem que dejó de re-listarse | Está resuelto. Devolvés fricción: el usuario tiene que salir a verificar algo ya cerrado |
| Reportar pendientes de otros proyectos | Los registros anotan pasos que se ejecutan en otro repo (tickets de clientes, el tracker). **Se descartan**: el briefing es de un proyecto solo |
