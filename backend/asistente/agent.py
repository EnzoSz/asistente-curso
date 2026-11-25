"""El agente, en dos versiones: la v1 (la de siempre) y la v2 (la candidata).

Es el archivo que la documentación de LangGraph llama agent.py: el que
arma el agente. No sabe nada de la web ni de la API: solo lo arma.

La v2 sale de lo que vimos en las trazas y en las evaluaciones:

    1. Instrucciones más precisas: cómo citar y qué decir cuando no
       encuentra algo (las fallas de honestidad y de cita de la clase 3).
    2. Barandas (middleware) para producción: ocultar correos, un tope de
       llamadas al modelo, reintentos de herramientas y un modelo de
       respaldo.

De acá salen:
    - agente y agente_v2: las dos versiones SIN memoria. Las usan
      langgraph.json y los pasos de la práctica.
    - armar_agente(version, checkpointer): para que la API arme la versión
      que le pidan, con su propia memoria en SQLite.

Concepto del sílabo: optimización continua a partir de trazas y
métricas de producción (Módulo 3, Semana 4).
"""

import os
import sys

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ModelFallbackMiddleware,
    PIIMiddleware,
    ToolRetryMiddleware,
)

from asistente.utils.tools import HERRAMIENTAS

load_dotenv()

# Gemini hace los embeddings del RAG (documentos.py); Anthropic es el
# modelo que contesta.
for clave in ("GOOGLE_API_KEY", "ANTHROPIC_API_KEY"):
    if not os.getenv(clave):
        print(f"Falta {clave} en el .env")
        sys.exit(1)

# El modelo que contesta: Claude Sonnet 5.5. Es el único lugar donde
# aparece: la API, las evaluaciones y los pasos lo importan.
MODELO = "claude-sonnet-5-5"
PROVEEDOR = "anthropic"
# El plan B de la v2, en OTRO proveedor: si Anthropic se cae, contesta Gemini.
MODELO_RESPALDO = "google_genai:gemini-3.8-flash"


# --- Versión 1: la que está en producción desde la clase 1 ------------
INSTRUCCIONES = (
    "Sos el asistente del Módulo 3 del curso de AI Agent Building. "
    "Atendés a alumnos con dudas sobre fechas, contenidos y el "
    "assignment. Para fechas usá el calendario; para todo lo demás, "
    "buscá en los documentos y citá el archivo entre corchetes. "
    "Límites: no inventes datos que no estén en los documentos; si no "
    "lo encontrás, decilo y sugerí consultar al docente. No hagas el "
    "assignment por el alumno: orientalo. Contestá en tres líneas "
    "como máximo."
)


# --- Versión 2: la candidata -------------------------------------------
INSTRUCCIONES_V2 = (
    "Sos el asistente del Módulo 3 del curso de AI Agent Building. "
    "Atendés a alumnos con dudas sobre fechas, contenidos y el "
    "assignment.\n"
    "Cómo trabajar:\n"
    "- Fechas: usá buscar_fecha y, si preguntan cuánto falta, "
    "contar_dias.\n"
    "- Todo lo demás: usá buscar_en_documentos ANTES de contestar.\n"
    "- Terminá cada respuesta con la fuente entre corchetes, con el "
    "nombre exacto del archivo, por ejemplo [silabo-modulo-3.md].\n"
    "- Si los fragmentos no tienen el dato, contestá exactamente: "
    "«No lo encontré en los documentos del curso; consultalo con el "
    "docente.» No completes con lo que sabés de otros cursos.\n"
    "- No hagas el assignment por el alumno: orientalo.\n"
    "- Como máximo tres líneas."
)

# Las barandas, en el orden en que actúan. Cada una resuelve un problema
# que vimos en las clases anteriores.
BARANDAS = [
    # Datos personales: los correos se reemplazan antes de llegar al
    # modelo y a las trazas.
    PIIMiddleware("email", strategy="redact", apply_to_input=True),
    # Costo y bucles: como máximo 5 llamadas al modelo por pregunta. Si
    # se pasa, termina con un aviso en vez de una excepción.
    ModelCallLimitMiddleware(run_limit=5, exit_behavior="end"),
    # APIs inestables (como un 503 de Gemini): si una herramienta falla,
    # reintenta dos veces. Si sigue fallando, le avisa al modelo.
    ToolRetryMiddleware(max_retries=2, initial_delay=0.5, on_failure="continue"),
    # Caídas del proveedor: si el modelo principal falla, usa este.
    ModelFallbackMiddleware(MODELO_RESPALDO),
]


def armar_agente(version: str = "v1", checkpointer=None):
    """Arma la versión pedida del agente ("v1" o "v2")."""
    if version == "v2":
        return create_agent(
            f"{PROVEEDOR}:{MODELO}",
            tools=HERRAMIENTAS,
            system_prompt=INSTRUCCIONES_V2,
            middleware=BARANDAS,
            checkpointer=checkpointer,
        )
    return create_agent(
        f"{PROVEEDOR}:{MODELO}",
        tools=HERRAMIENTAS,
        system_prompt=INSTRUCCIONES,
        checkpointer=checkpointer,
    )


# Las dos versiones sin memoria: para langgraph.json y los pasos.
agente = armar_agente("v1")
agente_v2 = armar_agente("v2")
