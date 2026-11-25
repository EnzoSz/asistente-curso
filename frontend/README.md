# Frontend - el chat web del asistente

Un chat en Streamlit que le habla al backend. **No tiene el agente ni las
claves**: solo sabe la dirección del backend (`URL_BACKEND`).

## Cómo arrancar (con el backend ya prendido)

```bash
uv sync
cp .env.example .env      # en Windows: Copy-Item .env.example .env
uv run streamlit run app.py
```

Abrí http://localhost:8501.

## Cómo funciona `app.py`

| Parte | Qué hace |
|---|---|
| `st.session_state` | Recuerda el `hilo_id` (la conversación) y los mensajes entre una ejecución y otra |
| Barra lateral | El nombre del alumno (viaja como metadato a LangSmith) y "Nueva conversación" |
| `st.chat_message` | Dibuja cada mensaje |
| `st.feedback("thumbs")` | El pulgar arriba o abajo: llama a `POST /feedback` |
| `st.chat_input` | La pregunta nueva: llama a `POST /preguntar` |

Streamlit vuelve a ejecutar `app.py` de arriba abajo cada vez que el usuario
hace algo. Por eso lo que hay que recordar va en `st.session_state`.

## ¿Y si algo falla?

| Lo que ves | Qué significa | Qué hacer |
|---|---|---|
| `ConnectionError` en la página | El backend no está prendido (o Render está dormido) | En tu computadora: `uv run fastapi dev api/main.py`. En la nube: abrí `/salud` del backend y esperá un minuto |
| `El backend respondió 401` | La `CLAVE_API` no coincide con la del backend | Copiala igual en los dos lados |
| La página no abre sola | Está configurado así en `.streamlit/config.toml` | Abrí http://localhost:8501 |
| `Port 8501 is already in use` | Otro Streamlit sigue abierto | Cerralo, o `uv run streamlit run app.py --server.port 8502` |

## Publicarlo en Streamlit Community Cloud

Create app > tu repositorio > Main file path `frontend/app.py`. En Advanced
settings, Python 3.12 y estos Secrets:

```toml
URL_BACKEND = "https://<tu-backend>.onrender.com"
CLAVE_API = "la-misma-que-en-render"
```

`app.py` lee cada valor primero del `.env` (en tu computadora) y si no está, de
los Secrets (en la nube). Instala solo, con el `uv.lock` de esta carpeta.
