# Setup MCP — Nivel Avanzado

Configuración para conectar **Claude Code** a los dos servidores MCP que se usan
en el módulo 2:

- **GitHub MCP** — el agente lee el repositorio en tiempo real.
- **Qdrant MCP** — el agente busca el código por intención (búsqueda semántica).

La configuración vive en el `.mcp.json` de esta carpeta y viaja con el repo, así
que alcanza con clonar, poner el token y aceptar.

---

## Requisitos previos

- **Docker Desktop corriendo** — lo usan los dos servidores.
- Python 3.10+ con `uv` instalado (`pip install uv`), para Qdrant.

---

## Paso 1 — Bajar las imágenes

Hacerlo **antes** de la sesión: la primera vez tarda, y con la sala esperando
tarda más.

```bash
docker pull ghcr.io/github/github-mcp-server:v1.12.0
docker pull qdrant/qdrant
```

---

## Paso 2 — Levantar Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

Verificar que responde: abrir `http://localhost:6333/dashboard` en el browser.
Dejarlo corriendo en su propia terminal.

El de GitHub **no hay que levantarlo a mano**: Claude Code corre el contenedor
solo, uno por sesión, y lo apaga al cerrar (`--rm`).

---

## Paso 3 — Obtener un GitHub Personal Access Token

1. Ir a `github.com → Settings → Developer settings → Personal access tokens → Fine-grained tokens`
2. Crear un token con estos permisos:
   - **Contents:** Read-only
   - **Metadata:** Read-only
3. Copiar el token generado

---

## Paso 4 — Exportar el token como variable de entorno

El `.mcp.json` **no lleva el token adentro**: lo lee de la variable
`GITHUB_PERSONAL_ACCESS_TOKEN`. Es a propósito — un archivo de configuración con
un token en texto plano se commitea solo, y ese archivo está trackeado en este
repo.

```bash
# Linux / Mac
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_...

# Windows (PowerShell)
$env:GITHUB_PERSONAL_ACCESS_TOKEN = "ghp_..."
```

La variable vive en esa terminal. Para que persista, ponela en tu `.bashrc` /
`.zshrc`, o en las variables de entorno del usuario en Windows.

En el `.mcp.json`, el `-e GITHUB_PERSONAL_ACCESS_TOKEN` **sin valor** es lo que
pasa la variable de tu shell al contenedor. Si la escribís con valor ahí, vuelve
a quedar el token en el archivo.

---

## Paso 5 — Abrir Claude Code y aprobar los servidores

```bash
cd avanzado
claude
```

La primera vez que se abre el proyecto, Claude Code **pregunta si se confía en
los servidores MCP del repo**. Hay que aceptar: un `.mcp.json` es código que
alguien más escribió y que se va a ejecutar en tu máquina, así que la pregunta
es sana. Vale la pena abrir el archivo y leerlo antes de decir que sí.

Después, verificar con:

```
/mcp
```

Tienen que aparecer `github` y `qdrant` como conectados. Si uno figura como
fallido, `/mcp` muestra el error.

---

## Qué dice el `.mcp.json` y por qué

El servidor de GitHub arranca con dos flags que no son decorativos:

| Flag | Qué hace | Por qué está |
|---|---|---|
| `--read-only` | Deshabilita todas las herramientas de escritura | El ejercicio es **leer** el repo. Nada de lo que hacemos necesita que el agente pueda abrir issues o pushear |
| `--toolsets context,repos` | Carga solo dos grupos de herramientas de los 21 disponibles | Cada herramienta habilitada ocupa ventana de contexto **antes de que escribas nada** |

Lo segundo es el punto que conecta con el módulo 1. El servidor trae 21
toolsets —`issues`, `pull_requests`, `actions`, `notifications`, `gists`…— y por
defecto habilita seis. Cada uno mete sus definiciones de herramientas en el
prompt del sistema, en toda sesión, se usen o no.

**El ejercicio:** correr `/context` con esta configuración, después cambiar a
`--toolsets all`, reiniciar y volver a correr `/context`. La diferencia es el
costo de tener herramientas "por las dudas".

```bash
# ver todos los grupos disponibles
docker run --rm ghcr.io/github/github-mcp-server:v1.12.0 --help
```

---

## Verificación rápida

Probar en el chat:

```
¿Qué endpoints tiene la API de la carpeta avanzado de este repositorio?
```

Si responde listando los endpoints de `main.py`, el GitHub MCP está funcionando.

```
Buscá en la colección "curso-ia-dev" código que maneje errores de recursos no encontrados.
```

Si responde con fragmentos de código relevantes, el Qdrant MCP está funcionando
—requiere haber indexado el código primero, ver abajo.

---

## Indexar el código en Qdrant

Decirle al agente en el chat:

```
Leé el contenido de avanzado/app/main.py y de avanzado/app/repository.py
del repositorio, y guardá cada uno en Qdrant en la colección "curso-ia-dev".
Usá el nombre del archivo como metadata.
```

El agente va a encadenar GitHub MCP (para leer) con Qdrant MCP (para guardar).
Ese encadenado es el punto del ejercicio: ninguna de las dos herramientas sola
resuelve el pedido.

---

## Si algo falla

| Síntoma | Causa probable |
|---|---|
| `github` figura como fallido en `/mcp` | Docker no está corriendo, o la variable `GITHUB_PERSONAL_ACCESS_TOKEN` no está exportada en **la terminal desde la que abriste Claude Code** |
| `qdrant` figura como fallido | El contenedor de Qdrant no está levantado, o el puerto 6333 está ocupado |
| Los servidores no aparecen | No se aceptó el prompt de confianza, o el servidor quedó deshabilitado. La elección se guarda **fuera del repo**, en `~/.claude.json` → `projects` → la ruta del proyecto (claves `hasTrustDialogAccepted`, `enabledMcpjsonServers`, `disabledMcpjsonServers`) |
| La búsqueda semántica no devuelve nada | Falta indexar el código en Qdrant (sección de arriba) |
