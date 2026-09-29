---
name: abrir-dia-jira
description: Arma la foto del equipo para arrancar el día a partir de Jira. Muestra en qué está cada persona, quién se quedó sin tareas en cola, qué venció, qué vence esta semana, qué tareas en curso no tienen movimiento hace días y qué tareas no tienen responsable. Usar cuando el usuario quiere abrir el día, pide el estado del equipo o pregunta en qué está cada uno.
---

# Skill: abrir-dia-jira

Arma un briefing de arranque del día con el estado del equipo en Jira, **por persona**. Responde la pregunta de todas las mañanas: *¿en qué está cada uno, quién se trabó y a quién hay que pasarle trabajo?*

**Es de solo lectura.** La skill no asigna, no mueve ni comenta tickets. Si detecta algo para resolver, lo propone al final y espera que el usuario lo pida.

## Configuración

Completar una vez. Es lo único que hay que tocar para usarla en otro equipo.

| Dato | Valor |
|---|---|
| Sitio de Jira | `<tu-sitio>.atlassian.net` |
| Espacios (claves de proyecto) | `<CLAVE1>, <CLAVE2>` |
| Días sin movimiento para marcar una tarea en curso | `3` |

**Equipo.** Una fila por persona. La columna *Tipo* sirve para separar internos de externos en el briefing.

| Persona | accountId de Jira | Tipo |
|---|---|---|
| `<Nombre Apellido>` | `<a completar>` | interno |
| `<Nombre Apellido>` | `<a completar>` | externo |

Si falta un accountId, la skill lo busca por nombre con la herramienta de usuarios del conector de Atlassian (`lookupJiraAccountId`) y **propone anotarlo en esta tabla**, para no volver a buscarlo cada mañana.

## Requisitos

- El **conector de Atlassian** (el MCP oficial) conectado, con un usuario que pueda ver los espacios de la configuración. La IA ve lo que ve ese usuario, ni más ni menos.
- Opcional: el conector de **Google Calendar**, para sumar la agenda del día.

## Comportamiento

1. **Fecha de hoy y semana en curso.** Tomar la fecha local y calcular el **lunes y el domingo** de esta semana como fechas explícitas (`2026-09-28` y `2026-10-04`). No usar `endOfWeek()` de JQL: Jira toma la semana de domingo a sábado y deja afuera lo que vence el domingo.

2. **Una sola consulta de tareas abiertas**, con la herramienta de búsqueda por JQL del conector (`searchJiraIssuesUsingJql`):

   ```
   project in (<ESPACIOS>) AND statusCategory != Done ORDER BY assignee, duedate
   ```

   Pedir **solo estos campos**: `summary`, `status`, `assignee`, `duedate`, `priority`, `updated`. Sin la lista de campos, cada ticket vuelve con la descripción entera y el costo en tokens se multiplica. Si la respuesta trae más de una página, seguir paginando hasta el final antes de contar.

3. **Una segunda consulta, de lo cerrado desde ayer:**

   ```
   project in (<ESPACIOS>) AND statusCategory = Done AND updated >= startOfDay(-1)
   ```

   Mismos campos.

4. **Clasificar en memoria**, sin volver a consultar:

   | Grupo | Criterio |
   |---|---|
   | **En curso** | `statusCategory` = En curso |
   | **En cola** | `statusCategory` = Por hacer, con responsable |
   | **Vencida** | `duedate` anterior a hoy |
   | **Vence esta semana** | `duedate` entre hoy y el domingo |
   | **Sin movimiento** | En curso, con `updated` más viejo que los días de la configuración |
   | **Sin responsable** | `assignee` vacío |

   Usar siempre la **categoría** del estado, no el nombre: cada espacio puede llamar distinto a sus estados ("Sprint activo", "En desarrollo", "En revisión") y la categoría es la misma.

5. **Cruzar contra la tabla del equipo.** Una persona de la tabla que no aparece en ninguna tarea abierta **no tiene trabajo asignado**, y es el dato más importante del briefing. No confundirla con una persona que sí tiene tareas pero ninguna en curso.

6. **Agenda del día**, si el conector de Google Calendar está disponible. Si no está o falla, decirlo en el bloque de agenda.

7. **Emitir el briefing** con el formato de abajo, y ofrecer las acciones sin ejecutarlas.

## Formato del briefing

```markdown
# Apertura del día — {fecha}

## Para resolver hoy
{Máximo 5 puntos, ordenados por urgencia: vencidas de prioridad alta,
personas sin trabajo asignado, tareas en curso trabadas. Cada punto dice
qué pasa, con qué ticket y qué decisión pide.}

## Equipo
| Persona | En curso | En cola | Vencidas | Sin movimiento | Nota |
|---|---|---|---|---|---|
{una fila por persona de la configuración, primero internos y después externos}

## Sin responsable
{clave, título, estado y vencimiento. Omitir la sección si no hay.}

## Vence esta semana
{clave, título, responsable y fecha, ordenado por fecha}

## Cerrado desde ayer
{clave, título y quién lo cerró. Omitir si no hay.}

## Agenda
{los eventos de hoy, o "no se pudo leer el calendario"}
```

## Reglas

- **No inventar.** Todo sale de las consultas. Si una consulta falla, decirlo en el bloque que corresponde: un briefing con un hueco marcado sirve, uno con datos de relleno no.
- **"Sin movimiento" mide cambios, no trabajo.** `updated` cambia con cualquier edición, también la de una automatización. Si el equipo tiene automatizaciones que comentan o editan tickets, avisar que la columna puede subestimar las tareas trabadas.
- **Solo lectura.** Las acciones van como propuesta al final ("¿Querés que le asigne AMC-5 a Federico?"). Se ejecutan solo si el usuario las pide, y con la skill ya terminada.
- **Pocas consultas y acotadas.** Dos búsquedas por JQL alcanzan. No recorrer los tickets de a uno ni pedir todos los campos.

## Errores comunes

| Error | Qué pasa |
|---|---|
| Filtrar por `resolution = Unresolved` | Si un estado cambió de categoría, puede quedar la resolución cargada y la tarea desaparece de los conteos. La categoría del estado no tiene ese problema |
| Usar `endOfWeek()` | La semana de Jira termina el sábado: lo que vence el domingo no aparece |
| Contar solo a quienes aparecen en las tareas | La persona sin trabajo asignado no aparece en ninguna consulta. Por eso hace falta la tabla del equipo |
| Consultar sin la lista de campos | Cada ticket trae la descripción entera: el mismo briefing cuesta varias veces más |
| Asignar o mover tickets "para ayudar" | La skill es de lectura. Una escritura sin pedido queda en el historial del ticket a nombre del usuario |
