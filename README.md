# Práctica Clase 4 - El asistente en producción, y cómo mejorarlo

Módulo 3, Semana 4 - Certificación Internacional en AI Agent Building
Docente: **Enzo Soliz**

La web de la clase 3 funcionaba en tu computadora. Hoy la llevamos a
**producción**: el backend a **Render** y el front a **Streamlit Community
Cloud**, los dos gratis y con una URL pública. Después cerramos el ciclo del
módulo: medimos lo que pasa en producción, armamos una **versión 2** del
agente, la comparamos con la v1 y, si gana, la publicamos.

```
alumno ──► Streamlit Cloud (frontend) ──► Render (backend: FastAPI + agente) ──► NVIDIA
                                                │
                                                └──► LangSmith, entorno production
```

| Carpeta | Qué es | Dónde se despliega |
|---|---|---|
| `backend/` | El agente (v1 y v2), la API y los pasos de la práctica | Render |
| `frontend/` | El chat web | Streamlit Community Cloud |

---

## 0. Antes de la clase

Creá tres cuentas gratis (las tres se pueden abrir con la de GitHub):

1. **GitHub**: github.com
2. **Render**: render.com
3. **Streamlit Community Cloud**: share.streamlit.io

Y revisá que tengas **git**: `git --version` (si no, bajalo de git-scm.com).

---

## 1. Probarlo en tu computadora

Igual que en la clase 3, en dos terminales:

```bash
# Terminal 1
cd backend
uv sync
cp .env.example .env          # en Windows: Copy-Item .env.example .env
uv run paso0_verificar_entorno.py
uv run fastapi dev api/main.py

# Terminal 2
cd frontend
uv sync
cp .env.example .env
uv run streamlit run app.py
```

Hacé una pregunta en http://localhost:8501. La primera vez, el backend crea
`backend/documentos.db` (los embeddings de los documentos): ese archivo lo vamos
a subir a GitHub para que Render no los vuelva a calcular.

---

## 2. Subir el proyecto a GitHub

Parado en `practica-clase-04/` (la carpeta que tiene `backend/` y `frontend/`):

```bash
git init
git add .
git status          # REVISÁ: no tiene que aparecer ningún .env
git commit -m "Asistente del curso: backend y frontend"
```

En github.com: **New repository**, un nombre (por ejemplo `asistente-del-curso`),
**sin** README ni .gitignore. GitHub te muestra tres comandos; son estos:

```bash
git remote add origin https://github.com/TU-USUARIO/asistente-del-curso.git
git branch -M main
git push -u origin main
```

| Comando | Qué hace |
|---|---|
| `git init` | Convierte la carpeta en un repositorio |
| `git add .` | Elige qué archivos van en la próxima "foto" (todos, menos los del `.gitignore`) |
| `git commit -m "..."` | Saca la foto, con un mensaje |
| `git push` | Sube las fotos a GitHub |

> Si en `git status` aparece un `.env`, **no sigas**: revisá el `.gitignore`.
> Una clave subida a GitHub hay que darla por perdida y generar otra.

---

## 3. El backend en Render

En render.com: **New > Web Service** > conectá GitHub > elegí tu repositorio.

| Campo | Valor |
|---|---|
| Name | `asistente-del-curso` (va a ser parte de la URL) |
| Language | Python 3 |
| Branch | `main` |
| Root Directory | `backend` |
| Build Command | `UV_PYTHON_INSTALL_DIR=.uv-python uv sync --frozen --no-dev --managed-python` |
| Start Command | `uv run --no-sync fastapi run api/main.py --port $PORT` |
| Instance Type | **Free** |

En **Environment Variables**, cargá:

| Variable | Valor |
|---|---|
| `NVIDIA_API_KEY` | tu clave de NVIDIA |
| `LANGSMITH_API_KEY` | tu clave de LangSmith |
| `LANGSMITH_TRACING` | `true` |
| `LANGSMITH_AGENT_ID` | `asistente-del-curso` |
| `LANGSMITH_AGENT_ENVIRONMENT` | `production` (en tu computadora es `local`) |
| `VERSION_AGENTE` | `v1` |
| `CLAVE_API` | una clave larga que inventes vos (la vas a poner también en el front) |

En **Advanced > Health Check Path**: `/salud`. Y **Deploy Web Service**.

Cuando termine, Render te da una URL como `https://asistente-del-curso-xxxx.onrender.com`.
Probala:

- `https://.../salud` tiene que devolver `{"estado": "ok", ...}`.
- `https://.../docs` es la documentación. Con `CLAVE_API` cargada, `/preguntar`
  contesta **401** si no mandás la clave: está protegida.

**Por qué el Build Command es largo:** Render trae su propio Python. Con
`--managed-python` usamos el de uv, el mismo de la clase, que sabe cargar la
extensión de SQLite de `documentos.db`; `UV_PYTHON_INSTALL_DIR` lo guarda dentro
de la carpeta del proyecto, para que siga ahí cuando el servicio arranca.

---

## 4. El front en Streamlit Community Cloud

En share.streamlit.io: **Create app** y elegí desplegar desde GitHub.

| Campo | Valor |
|---|---|
| Repository | tu repositorio |
| Branch | `main` |
| Main file path | `frontend/app.py` |
| App URL | el nombre que quieras: `algo.streamlit.app` |

En **Advanced settings**: Python 3.12, y en **Secrets**:

```toml
URL_BACKEND = "https://asistente-del-curso-xxxx.onrender.com"
CLAVE_API = "la-misma-que-pusiste-en-render"
```

**Deploy**. Abrí la URL y preguntá. Esa URL es la que va en tu informe.

---

## 5. Lo que cambia en producción

| En tu computadora | En la nube |
|---|---|
| `.env` | Environment (Render) y Secrets (Streamlit) |
| `fastapi dev` | `fastapi run` |
| Entorno `local` en LangSmith | Entorno `production` |
| API abierta | Protegida con `CLAVE_API` |
| Siempre prendida | Render gratis **se duerme** a los 15 minutos sin uso: la primera pregunta tarda cerca de un minuto |
| `memoria.db` se guarda | El disco de Render gratis **se borra** al reiniciar o dormirse: las conversaciones se pierden (en serio: PostgreSQL) |

**Actualizar es un `git push`:** Render y Streamlit se vuelven a desplegar solos
con cada cambio que subís.

---

## 6. Bloque 2: optimización continua

Todos los pasos se corren parado en `backend/`, en tu computadora.

| Paso | Qué hace |
|---|---|
| `paso1_metricas_de_produccion.py` | Volumen, errores, latencia, tokens, costo, calidad y herramientas del entorno **production** (tu web desplegada) |
| `paso2_comparar_versiones.py` | La v1 y la v2 rinden el examen de la clase 3 |
| `paso3_barandas.py` | Datos personales, una API caída y un tope de llamadas |
| `paso4_de_produccion_al_dataset.py` | Las consultas con pulgar abajo pasan al próximo examen |

Necesitás el dataset `asistente-del-curso-preguntas` (clase 3, paso 1) y
algunas consultas en la web desplegada, con pulgares arriba y abajo.

### Qué cambia en la v2

| Problema que vimos | Clase | Cambio en la v2 |
|---|---|---|
| No siempre cita el archivo | 3 (`cita_la_fuente`) | Las instrucciones piden la fuente al final, con un ejemplo |
| A veces inventa en vez de decir que no sabe | 3 (`honestidad`) | Las instrucciones dan la frase exacta para «no lo encontré» |
| Datos personales en las trazas | 2 | `PIIMiddleware`: oculta los correos |
| Bucles y costo sin control | 2 | `ModelCallLimitMiddleware`: 5 llamadas como máximo |
| Una API caída rompe todo (o un 503 de NVIDIA) | 2 y 3 | `ToolRetryMiddleware`: reintenta y avisa |
| El proveedor se cae | - | `ModelFallbackMiddleware`: un modelo de respaldo |

### Publicar la v2

Si en el paso 2 la v2 gana: en Render, **Environment** > `VERSION_AGENTE` = `v2`
> **Save, rebuild and deploy**. Sin tocar código. `https://.../salud` te dice qué
versión está atendiendo, y cada traza lleva la versión como metadato: en
LangSmith podés comparar la v1 y la v2 **en producción**.

### Bonus: las dos versiones en el Agent Server

```bash
uv run langgraph dev
```

En Studio podés elegir `asistente` o `asistente_v2`.

---

## 7. Reto para casa

1. **Tu v3.** Cambiá algo de la v2 en `asistente/agent.py` (las instrucciones,
   el modelo o el tope de llamadas), corré el paso 2 y decidí si se publica.
2. **Un dashboard.** En LangSmith, entorno Production: consultas por día,
   latencia p95 y porcentaje de errores, agrupados por `version`. Es evidencia
   para el punto 5.
3. **Una alerta.** Que avise si los errores pasan el 20 % en 15 minutos.

---

## 8. ¿Y si algo falla?

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| `git push` pide usuario y contraseña | GitHub ya no acepta la contraseña | Usá un token (GitHub > Settings > Developer settings) o GitHub Desktop |
| Un `.env` en `git status` | El `.gitignore` no lo está dejando afuera | No hagas commit. Revisá que el archivo se llame exactamente `.env` |
| Render: `No module named 'api'` | El Root Directory no es `backend` | Settings > Root Directory: `backend` |
| Render: `Port scan timeout` | El Start Command no usa `$PORT` | Copiá el Start Command de la tabla |
| Render: `no such module: vec0` o `enable_load_extension` | Render usó su Python | Copiá el Build Command completo, con `--managed-python` |
| Streamlit: `ConnectionError` | `URL_BACKEND` mal escrita, o Render dormido | Revisá los Secrets; abrí `/salud` del backend y esperá un minuto |
| Streamlit: `401` | La `CLAVE_API` del front no es la de Render | Que sean iguales, letra por letra |
| `No hay ejecuciones` en el paso 1 | Nadie usó la web desplegada todavía | Hacé preguntas en tu URL de Streamlit, o cambiá `ENTORNO` |
| `Dataset ... not found` en el paso 2 | Falta el dataset de la clase 3 | Corré el paso 1 de la clase 3 |
| `429` o `503` en el paso 2 | NVIDIA está saturado | Bajá `max_concurrency` a `1` y probá en unos minutos |
| El paso 4 no encuentra consultas | No hay pulgares abajo en production | Dejá pulgares abajo en la web desplegada |
