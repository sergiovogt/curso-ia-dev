# Buenas Prácticas para la Optimización de Tokens en Cursor IDE

### Guía de Ingeniería de Prompts e Infraestructura para Equipos de Desarrollo

> **Nota de Arquitectura:** En Cursor, la gestión de tokens no es solo un factor de costes; impacta directamente en la **latencia de respuesta** y en la **precisión del modelo**. Rellenar innecesariamente la ventana de contexto provoca respuestas lentas, genéricas o propensas a la alucinación.

---

## 1. Control Quirúrgico del Contexto Manual

El error más común es asumir que la IA necesita leer todo el repositorio para resolver un problema puntual. Mantener el contexto limpio garantiza respuestas rápidas y precisas.

* **Evitar el uso indiscriminado de `@Codebase`:** No fuerces al IDE a vectorizar e indexar todo el proyecto para consultas locales o específicas. Si conoces los archivos implicados en la tarea, invócalos de forma explícita usando `@nombre_del_archivo`.
* **Acotación por rangos con `@Line Range`:** Para refactorizar o analizar funciones específicas dentro de archivos extensos (ej. más de 500 líneas), selecciona únicamente las líneas afectadas antes de abrir `Cmd/Ctrl + K` o `Cmd/Ctrl + L`. Cursor aislará ese fragmento minimizando el consumo de la ventana de contexto.
* **Ciclo de limpieza de hilos del Chat:** El historial acumulado en la pestaña de chat (`Cmd/Ctrl + L`) envía de forma recurrente los inputs y outputs anteriores en cada nuevo mensaje. Al cambiar de tarea, corregir un bug independiente o pivotar el enfoque, inicializa un chat limpio usando `Cmd/Ctrl + N`.

---

## 2. Eficiencia Estructural mediante Configuración

Automatizar qué ve y qué no ve la IA desde las raíces del proyecto ahorra miles de tokens diarios por desarrollador.

* **Centralización de instrucciones en `.cursorrules`:** Evita el *Prompt Stuffing* (repetir en cada instrucción el stack técnico, las reglas de formateo o patrones de diseño). Define las directrices de arquitectura, convenciones de tipado y estilo una sola vez en el archivo `.cursorrules` de la raíz del proyecto.
> 💡 **Ejemplo de optimización:** En lugar de escribir *"Usa TypeScript estricto, arquitectura limpia y componentes funcionales"* en cada prompt, tenerlo en las reglas del sistema consume menos tokens operativos por interacción y se aplica por defecto.


* **Sincronización estricta del `.gitignore`:** Cursor hereda las exclusiones del control de versiones. Asegúrate de incluir correctamente directorios de compilación (`dist/`, `.next/`, `node_modules/`), artefactos pesados, logs o imágenes para impedir que el indexador en segundo plano procese e inyecte data irrelevante en las búsquedas globales.

---

## 3. Uso Avanzado de Composer y Agentes Autónoma

Las herramientas multi-archivo de Cursor son muy potentes, pero si se configuran mal pueden entrar en bucles infinitos de consumo de tokens.

* **Pre-validación con *Plan Mode*:** En modificaciones complejas que afecten a múltiples archivos (`Cmd/Ctrl + I`), exige siempre la creación de un plan en Markdown antes de permitir que la IA ejecute cambios en el código. Validar la estrategia de manera estática con el equipo evita ciclos repetitivos de escritura/error que duplican el consumo de tokens de salida.
* **Delimitación de objetivos para *Cloud Agents*:** Al delegar una tarea autónoma al Agente, define límites estrictos de alcance. En lugar de instrucciones ambiguas como *"Mejora los módulos de la aplicación"*, utiliza restricciones precisas: *"Modifica únicamente las funciones de mapeo y tipos dentro de la carpeta `/src/repositories`"*.

---

## 4. Selección de Modelos Asimétricos

No todos los problemas requieren el modelo más potente del mercado. El enrutamiento inteligente de tareas define la eficiencia del equipo.

* **Asignación de modelos según la complejidad técnica:**
* **Cursor Tab (Autocompletado):** Mantenerlo siempre activo. Utiliza modelos nativos optimizados de bajísima huella y respuesta inmediata.
* **Tareas Complejas (Debug a ciegas, refactorización estructural, lógica compleja):** Utilizar `Claude 3.5 Sonnet` o `GPT-4o/5`. Tienen ventanas de contexto masivas y alta capacidad de razonamiento.
* **Tareas Mecánicas (Escribir documentación, crear tests unitarios simples, conversiones de formato):** Cambiar el selector del chat a modelos más rápidos y económicos como `Gemini Flash` o versiones `Mini`. Resuelven la tarea con la misma eficacia por una fracción del costo en tokens.



---

> 📌 **Mantra del equipo:** *"En el desarrollo guiado por IA, un token ahorrado es un milisegundo ganado. Acotar el contexto óptimo garantiza respuestas inmediatas y código de alta fidelidad."*