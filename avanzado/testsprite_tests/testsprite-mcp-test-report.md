# TestSprite AI Testing Report(MCP)

---

## 1️⃣ Document Metadata
- **Project Name:** avanzado
- **Date:** 2026-09-22
- **Prepared by:** TestSprite AI Team
- **Tipo de test:** backend (API JSON + rutas `/ui/`)
- **Endpoint bajo prueba:** http://localhost:8010
- **Alcance de esta corrida:** un solo caso (TC009) del plan de 10

---

## 2️⃣ Requirement Validation Summary

### Requisito: Acciones de la página web (rutas `/ui/`)
- **Descripción:** Las acciones de la página server-rendered se hacen por POST de
  formulario y redirigen con `303 See Other` a `/`. No hay login.

#### Test TC009 post ui tasks complete and delete redirect even if task not found
- **Test Code:** [TC009_post_ui_tasks_complete_and_delete_redirect_even_if_task_not_found.py](./TC009_post_ui_tasks_complete_and_delete_redirect_even_if_task_not_found.py)
- **Test Visualization and Result:** https://www.testsprite.com/dashboard/mcp/tests/612d543c-4ad7-5abf-b720-10f04c0a94b2/test/a1fce561-f27b-4386-b02d-47cf61b9fb8a
- **Status:** ✅ Passed
- **Analysis / Findings:** El test verificó cuatro POSTs sin seguir redirects
  (`allow_redirects=False`), que es lo que hace significativo el resultado: se comprueba el
  `303` en sí mismo y el header `Location`, no la página final.

  | Caso | Request | Resultado |
  |---|---|---|
  | id inexistente | `POST /ui/tasks/999999/complete` | 303, `Location: /` |
  | id inexistente | `POST /ui/tasks/999999/delete` | 303, `Location: /` |
  | id existente | `POST /ui/tasks/{id}/complete` | 303, `Location: /` |
  | id existente | `POST /ui/tasks/{id}/delete` | 303, `Location: /` |

  El caso "id existente" usó una tarea creada por el propio test vía `POST /tasks`, no las
  sembradas (ids 1–5). El cleanup final (`DELETE /tasks/{id}`) aceptó 204 o 404, correcto:
  la tarea ya había sido borrada por la ruta `/ui/`.

  **Lo que el test confirma es una carencia deliberada, no una corrección.** `ui_complete_task`
  y `ui_delete_task` ([app/main.py:49](../app/main.py#L49) y [app/main.py:55](../app/main.py#L55))
  llaman a `repo.mark_complete()` / `repo.delete()` e ignoran el valor de retorno, así que
  devuelven 303 sin distinguir si el id existía. El contraste con la API JSON es el punto:
  `DELETE /tasks/{id}` sí levanta `HTTPException` 404 con `"Tarea con id {id} no encontrada"`.
  Este caso documenta el comportamiento actual (test de caracterización); no debe leerse como
  validación de que el comportamiento sea el deseado.

---

## 3️⃣ Coverage & Matching Metrics

- **100.00%** de los tests ejecutados pasaron (1 de 1)
- **10.00%** del plan de backend fue ejecutado (1 de 10 casos)

| Requirement | Total Tests | ✅ Passed | ❌ Failed |
|---|---|---|---|
| Acciones de la página web (rutas `/ui/`) | 1 | 1 | 0 |
| **Total ejecutado** | **1** | **1** | **0** |

Casos del plan **no ejecutados** en esta corrida: TC001–TC008 y TC010.

---

## 4️⃣ Key Gaps / Risks

1. **La cobertura de esta corrida es de un solo caso.** El 100% de aprobación aplica a TC009
   únicamente. Los nueve casos restantes del plan —CRUD JSON, validaciones 422, filtros y
   orden, render HTML, migración y seed— siguen sin ejecutarse. No hay evidencia todavía
   sobre el grueso de la API.

2. **Las rutas `/ui/` no distinguen id inexistente.** Confirmado por TC009: un complete o un
   delete sobre un id que no existe se ve idéntico a uno exitoso desde el cliente. Es
   material intencional del curso, pero si alguna vez se decide corregirlo, TC009 es
   exactamente el test que va a romper — conviene saberlo antes de tocarlo.

3. **TC010 no es verificable por HTTP.** Ese caso cubre migración y seed de `tasks.db`, que
   requiere reiniciar la app y manipular el archivo de base. Ejecutado contra el servidor
   corriendo va a quedar inconcluso o fallar por razones ajenas al código bajo prueba.

4. **Los tests corren contra `tasks.db` real, no contra una base temporal.** A diferencia de
   la suite de `pytest` en `tests/`, esta corrida toca la base sembrada. TC009 se comportó
   bien (creó y limpió su propia tarea, y la base quedó en 5 tareas con los estados del
   seed), pero otros casos del plan —sobre todo los de DELETE y PUT— pueden alterar el estado
   de demo. Para volver al estado inicial: borrar `tasks.db` y reiniciar la app.

---
