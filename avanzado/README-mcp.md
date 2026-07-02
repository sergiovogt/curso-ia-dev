# Setup MCP — Nivel Intermedio

Configuración para conectar Cursor y VS Code a los dos servidores MCP usados en la capacitación #3:
- **GitHub MCP** — la IA lee el repositorio en tiempo real
- **Qdrant MCP** — la IA busca el código por intención (búsqueda semántica)

---

## Requisitos previos

- Node.js 18+ (para `npx`)
- Python 3.10+ con `uv` instalado (`pip install uv`)
- Docker Desktop corriendo

---

## Paso 1 — Levantar Qdrant con Docker

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Verificar que responde: abrir `http://localhost:6333/dashboard` en el browser.

---

## Paso 2 — Obtener un GitHub Personal Access Token

1. Ir a `github.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens`
2. Crear un token con estos permisos:
   - **Contents:** Read-only
   - **Metadata:** Read-only
3. Copiar el token generado

---

## Paso 3a — Configurar en Cursor

1. Copiar `.cursor/mcp.json` de esta carpeta a la raíz del repo (o usarlo desde acá si Cursor lo detecta)
2. Abrir `.cursor/mcp.json` y reemplazar `TU_TOKEN_AQUI` por el token de GitHub
3. Reiniciar Cursor
4. Verificar en `Cursor → Settings → MCP` que aparecen los dos servidores con estado activo

---

## Paso 3b — Configurar en VS Code

1. Asegurarse de tener la extensión **GitHub Copilot** instalada y activa
2. La carpeta `.vscode/mcp.json` ya está lista — VS Code la detecta automáticamente
3. Al abrir Copilot Chat en modo agente, pedirá el token de GitHub la primera vez

---

## Verificación rápida

Una vez configurado, probar en el chat del IDE:

```
¿Qué endpoints tiene la API de la carpeta intermedio de este repositorio?
```

Si responde correctamente listando los endpoints de `main.py`, el GitHub MCP está funcionando.

```
Buscá en la colección "curso-ia-dev" código que maneje errores de recursos no encontrados.
```

Si responde con fragmentos de código relevantes, el Qdrant MCP está funcionando (requiere haber indexado el código primero — ver más abajo).

---

## Indexar el código en Qdrant

Decirle al modelo en el chat:

```
Leé el contenido de intermedio/app/main.py y de intermedio/app/repository.py 
del repositorio, y guardá cada uno en Qdrant en la colección "curso-ia-dev". 
Usá el nombre del archivo como metadata.
```

El modelo va a encadenar GitHub MCP (para leer) con Qdrant MCP (para guardar).
