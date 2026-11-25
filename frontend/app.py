"""El front del asistente: un chat web hecho con Streamlit.

Qué hace: muestra un chat en el navegador y, por cada mensaje, le
pregunta al backend (la API de FastAPI). El front NO tiene el agente ni
las claves: solo sabe la dirección del backend. Si mañana cambiás el
modelo o las herramientas, el front no se entera.

Streamlit funciona distinto a un programa común: cada vez que el usuario
hace algo (escribe, toca un botón), el script se vuelve a ejecutar de
arriba abajo. Lo que hay que recordar entre una ejecución y la otra se
guarda en st.session_state.

Cómo se ejecuta (con el backend prendido en OTRA terminal):
    uv run streamlit run app.py

En Streamlit Community Cloud, la configuración (URL_BACKEND y CLAVE_API)
se carga en Secrets en vez del .env.
"""

import os
import uuid

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


def configuracion(nombre: str, por_defecto: str = "") -> str:
    """Lee un valor del .env (en tu computadora) o de los Secrets de
    Streamlit Community Cloud (en la nube)."""
    valor = os.getenv(nombre)
    if valor:
        return valor
    try:
        return st.secrets.get(nombre, por_defecto)
    except Exception:  # en tu computadora no hay archivo de secrets
        return por_defecto


# La dirección del backend. En tu computadora, el de fastapi dev. En la
# nube, la URL que te dio Render.
URL_BACKEND = configuracion("URL_BACKEND", "http://127.0.0.1:8000").rstrip("/")
# La clave de la API, si el backend la pide (la misma CLAVE_API de Render).
ENCABEZADOS = {"X-API-Key": configuracion("CLAVE_API")}

st.set_page_config(page_title="Asistente del curso")
st.title("Asistente del curso")
st.caption("Módulo 3 · AI Agent Building")


# --- Lo que se recuerda entre ejecuciones ----------------------------
# hilo_id: una conversación por pestaña del navegador (el thread_id).
# mensajes: lo que se ve en pantalla.
if "hilo_id" not in st.session_state:
    st.session_state.hilo_id = str(uuid.uuid4())
    st.session_state.mensajes = []


# --- La barra lateral --------------------------------------------------
with st.sidebar:
    alumno = st.text_input("Tu nombre", value="anonimo")
    if st.button("Nueva conversación"):
        st.session_state.hilo_id = str(uuid.uuid4())
        st.session_state.mensajes = []
    st.caption(f"Conversación: {st.session_state.hilo_id[:8]}")
    st.caption(f"Backend: {URL_BACKEND}")


# --- La conversación hasta ahora --------------------------------------
for i, mensaje in enumerate(st.session_state.mensajes):
    with st.chat_message(mensaje["rol"]):
        st.write(mensaje["texto"])

        # Debajo de cada respuesta, el pulgar arriba o abajo. Lo que
        # elige el alumno viaja al backend, y de ahí a LangSmith.
        if mensaje["rol"] == "assistant":
            opinion = st.feedback("thumbs", key=f"opinion-{i}")
            if opinion is not None and not mensaje.get("opinion_enviada"):
                requests.post(
                    f"{URL_BACKEND}/feedback",
                    json={"run_id": mensaje["run_id"], "le_sirvio": opinion == 1},
                    headers=ENCABEZADOS,
                    timeout=30,
                )
                mensaje["opinion_enviada"] = True


# --- Una pregunta nueva -----------------------------------------------
pregunta = st.chat_input("Preguntá sobre el curso...")

if pregunta:
    st.session_state.mensajes.append({"rol": "user", "texto": pregunta})
    with st.chat_message("user"):
        st.write(pregunta)

    with st.chat_message("assistant"):
        # En el plan gratis de Render, si nadie usó la API en 15 minutos,
        # se duerme: la primera pregunta tarda cerca de un minuto.
        with st.spinner("Pensando... (la primera vez puede tardar un minuto)"):
            respuesta = requests.post(
                f"{URL_BACKEND}/preguntar",
                json={
                    "pregunta": pregunta,
                    "hilo_id": st.session_state.hilo_id,
                    "alumno": alumno,
                },
                headers=ENCABEZADOS,
                timeout=180,
            )
        if respuesta.status_code != 200:
            # Un error del backend se muestra, en vez de romper la página.
            st.error(f"El backend respondió {respuesta.status_code}: {respuesta.text}")
            st.stop()
        datos = respuesta.json()
        st.write(datos["respuesta"])

    st.session_state.mensajes.append(
        {"rol": "assistant", "texto": datos["respuesta"], "run_id": datos["run_id"]}
    )
    # Volvemos a dibujar la página para que aparezcan los pulgares.
    st.rerun()
