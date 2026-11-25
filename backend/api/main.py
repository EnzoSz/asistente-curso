"""La API del asistente, lista para producción.

Qué hace: publica el agente en tres direcciones (endpoints):

    GET  /salud      ¿la API está viva? (Render la usa para saberlo)
    POST /preguntar  el alumno pregunta, el agente contesta
    POST /feedback   el alumno dice si la respuesta le sirvió

Es la API de la clase 3, con tres cosas nuevas para la nube. Las tres se
configuran con variables de entorno, sin tocar el código:

    - VERSION_AGENTE: qué versión atiende, "v1" o "v2". Publicar la v2 es
      cambiar esta variable en Render.
    - CLAVE_API: si tiene un valor, solo atiende pedidos que traigan esa
      clave en el encabezado X-API-Key. Así nadie más gasta tus tokens.
    - LANGSMITH_AGENT_ENVIRONMENT: "local" en tu computadora y
      "production" en Render. Mismo código, trazas separadas.

Cómo se ejecuta (parado en backend/):
    uv run fastapi dev api/main.py      # en tu computadora
    uv run fastapi run api/main.py      # en la nube
"""

import os
import sqlite3
import uuid

import langsmith as ls
from fastapi import Depends, FastAPI, Header, HTTPException
from langgraph.checkpoint.sqlite import SqliteSaver

from api.esquemas import Opinion, Pregunta, Respuesta
from asistente.agent import MODELO, armar_agente

VERSION_AGENTE = os.getenv("VERSION_AGENTE", "v1")
CLAVE_API = os.getenv("CLAVE_API", "")

# A qué agente y entorno de LangSmith van las trazas (lo dice el entorno).
DESTINO = ls.agent_address(
    os.getenv("LANGSMITH_AGENT_ID", "asistente-del-curso"),
    os.getenv("LANGSMITH_AGENT_ENVIRONMENT", "local"),
)

# --- La memoria: un archivo SQLite -----------------------------------
# check_same_thread=False: FastAPI atiende pedidos en varios hilos del
# procesador a la vez, y todos usan la misma conexión. En el plan gratis
# de Render el disco se borra al reiniciar: las conversaciones se pierden.
conexion = sqlite3.connect("memoria.db", check_same_thread=False)
memoria = SqliteSaver(conexion)

agente = armar_agente(VERSION_AGENTE, checkpointer=memoria)
cliente_langsmith = ls.Client()

app = FastAPI(
    title="Asistente del curso",
    description="El agente del Módulo 3, como API web.",
    version="2.0.0",
)


# --- La clave de la API ------------------------------------------------
# Una "dependencia" de FastAPI: una función que corre antes de la ruta.
# Si no hay CLAVE_API configurada (en tu computadora), deja pasar todo.
def verificar_clave(x_api_key: str = Header(default="")):
    if CLAVE_API and x_api_key != CLAVE_API:
        raise HTTPException(status_code=401, detail="Falta la clave de la API")


@app.get("/salud")
def salud():
    """Responde si la API está funcionando, con qué modelo y qué versión."""
    return {"estado": "ok", "modelo": MODELO, "version": VERSION_AGENTE}


@app.post(
    "/preguntar",
    response_model=Respuesta,
    dependencies=[Depends(verificar_clave)],
)
def preguntar(pedido: Pregunta):
    """Le pasa la pregunta al agente, en el hilo de esa conversación."""
    # El id de la traza lo elegimos nosotros: así el front puede mandar
    # el feedback de ESTA respuesta después.
    run_id = uuid.uuid4()

    resultado = agente.invoke(
        {"messages": [{"role": "user", "content": pedido.pregunta}]},
        config={
            "configurable": {"thread_id": pedido.hilo_id},
            "run_id": run_id,
            "run_name": "consulta-web",
            "tags": ["web", VERSION_AGENTE],
            # La versión viaja como metadato: en LangSmith se pueden
            # comparar las métricas de la v1 y de la v2 en producción.
            "metadata": {
                "alumno": pedido.alumno,
                "canal": "web",
                "version": VERSION_AGENTE,
            },
        },
    )
    respuesta = resultado["messages"][-1].text

    # Las herramientas de ESTA pregunta: lo que vino después del último
    # mensaje del alumno (el hilo trae también las preguntas anteriores).
    herramientas = []
    for mensaje in reversed(resultado["messages"]):
        if mensaje.type == "human":
            break
        if mensaje.type == "ai":
            for llamada in mensaje.tool_calls:
                herramientas.insert(0, llamada["name"])

    # Evaluación online (clase 3): dos criterios sin respuesta esperada.
    lineas = [linea for linea in respuesta.splitlines() if linea.strip()]
    es_breve = len(lineas) <= 3
    cita_fuente = ".md" in respuesta or "buscar_fecha" in herramientas

    cliente_langsmith.create_feedback(
        run_id,
        key="es_breve",
        score=int(es_breve),
        trace_id=run_id,
        address=DESTINO,
    )
    cliente_langsmith.create_feedback(
        run_id,
        key="cita_fuente",
        score=int(cita_fuente),
        trace_id=run_id,
        address=DESTINO,
    )

    return Respuesta(
        respuesta=respuesta,
        hilo_id=pedido.hilo_id,
        run_id=str(run_id),
        herramientas=herramientas,
    )


@app.post("/feedback", dependencies=[Depends(verificar_clave)])
def feedback(opinion: Opinion):
    """Guarda en LangSmith si la respuesta le sirvió al alumno."""
    cliente_langsmith.create_feedback(
        opinion.run_id,
        key="le_sirvio",
        score=int(opinion.le_sirvio),
        comment=opinion.comentario,
        trace_id=opinion.run_id,
        address=DESTINO,
    )
    return {"guardado": True}
