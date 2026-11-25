# Backend - el asistente en producción

El agente del curso (v1 y v2) y su API con FastAPI. Es la carpeta que se
despliega en **Render**. Acá viven las claves, la memoria y los pasos de la
práctica. Los pasos para desplegar están en el `README.md` de
`practica-clase-04`.

```
backend/
├── asistente/                 el agente (estructura de LangGraph)
│   ├── agent.py               v1, v2 (con BARANDAS) y armar_agente()
│   └── utils/
│       ├── tools.py           buscar_fecha, contar_dias, buscar_en_documentos
│       └── documentos.py      la base vectorial, guardada en documentos.db
├── api/                       la API (FastAPI)
│   ├── main.py                GET /salud, POST /preguntar, POST /feedback
│   └── esquemas.py            qué entra y qué sale (Pydantic)
├── documentos/                lo que consulta el RAG
├── evaluadores.py             los cuatro criterios de la clase 3
├── paso0 a paso4              diagnóstico y optimización continua
├── langgraph.json             las dos versiones, también para el Agent Server
├── .python-version            Python 3.12, en tu computadora y en Render
└── pyproject.toml, uv.lock, .env.example
```

---

## 1. Cómo arrancar (en tu computadora)

```bash
uv sync
cp .env.example .env      # en Windows: Copy-Item .env.example .env
uv run paso0_verificar_entorno.py
uv run fastapi dev api/main.py
```

En http://127.0.0.1:8000/docs está la documentación interactiva.

---

## 2. Lo nuevo de la API: tres variables de entorno

La API es la de la clase 3. Lo que cambia entre tu computadora y Render no es el
código: son las variables de entorno.

| Variable | En tu computadora (`.env`) | En Render (Environment) | Para qué |
|---|---|---|---|
| `LANGSMITH_AGENT_ENVIRONMENT` | `local` | `production` | Separar tus pruebas del uso real |
| `VERSION_AGENTE` | `v1` (o `v2` para probar) | `v1`, y `v2` cuando gane | Qué versión atiende |
| `CLAVE_API` | vacía (API abierta) | una clave larga | Que nadie más use tu API |

Con `CLAVE_API` cargada, `/preguntar` y `/feedback` piden el encabezado
`X-API-Key`. En `/docs` no lo vas a poder probar sin él: eso es lo que queremos.
`/salud` queda abierta (Render la usa para saber si la API está viva) y dice
qué versión está atendiendo.

---

## 3. Los endpoints

| Endpoint | Recibe | Devuelve |
|---|---|---|
| `GET /salud` | nada | `{"estado": "ok", "modelo": ..., "version": ...}` |
| `POST /preguntar` | `pregunta`, `hilo_id`, `alumno` (+ `X-API-Key`) | `respuesta`, `hilo_id`, `run_id`, `herramientas` |
| `POST /feedback` | `run_id`, `le_sirvio`, `comentario` (+ `X-API-Key`) | `{"guardado": true}` |

Cada traza `consulta-web` lleva como metadatos el alumno, el canal y la
**versión** del agente.

---

## 4. Los pasos de la práctica

| Script | Qué hace |
|---|---|
| `paso1_metricas_de_produccion.py` | El tablero del entorno production: volumen, errores, latencia, costo, calidad y herramientas |
| `paso2_comparar_versiones.py` | La v1 y la v2 rinden el mismo examen |
| `paso3_barandas.py` | Las barandas de la v2, una por una |
| `paso4_de_produccion_al_dataset.py` | Las consultas con pulgar abajo, a un dataset para revisar |

Los pasos usan el agente de `asistente/agent.py` directamente, sin pasar por
la API. Se corren en tu computadora, con tu `.env`.

---

## 5. También como Agent Server

```bash
uv run langgraph dev
```

En Studio podés elegir `asistente` (v1) o `asistente_v2`.

---

## 6. ¿Y si algo falla?

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| `ModuleNotFoundError: No module named 'asistente'` | No estás parado en `backend/` | `cd backend` |
| `401 Falta la clave de la API` | `CLAVE_API` tiene valor y el pedido no trae la clave | Mandá `X-API-Key`, o dejá `CLAVE_API` vacía en tu `.env` |
| `Address already in use` | Otro programa usa el puerto 8000 | `uv run fastapi dev api/main.py --port 8001` |
| `500 Internal Server Error` | Falló algo adentro (el modelo, LangSmith) | Mirá la terminal de la API (en Render: **Logs**) |
| `no such module: vec0` o `enable_load_extension` | Tu Python no carga extensiones de SQLite | `uv python install 3.12` y `uv sync` |
| `404` del modelo de respaldo | No está disponible para tu cuenta | Cambiá `MODELO_RESPALDO` en `asistente/agent.py` |
| `Unable to configure formatter 'simple'` (Windows) | Falta `colorama` | `uv sync` con la carpeta actualizada |
