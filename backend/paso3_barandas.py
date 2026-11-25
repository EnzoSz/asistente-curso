"""Paso 3: las barandas de la v2, una por una.

Qué demuestra: un agente en producción tiene que fallar bien. La
lectura de PwC de esta semana lo dice así: los agentes pierden el rumbo,
y hay que ponerles límites antes de que pase. Probamos tres barandas
(middleware) con los problemas que vimos en la clase 2:

    1. Datos personales: un correo en la pregunta no llega al modelo.
    2. Una API caída: la herramienta de feriados con el tiempo máximo
       ridículo de la clase 2. Antes rompía todo; ahora el agente
       reintenta, y si no puede, le avisa al alumno.
    3. Un tope de llamadas al modelo: en vez de una excepción, el
       agente termina con un aviso.

Concepto del sílabo: optimización continua; análisis de patrones de
falla (Módulo 3, Semana 4).

Cómo se ejecuta:
    uv run paso3_barandas.py
"""

import requests
from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.tools import tool
from langchain_core.tracers.langchain import wait_for_all_tracers

from asistente.agent import BARANDAS, MODELO, PROVEEDOR, agente_v2
from asistente.utils.tools import buscar_fecha

# El mismo tiempo máximo de la clase 2: ninguna API contesta tan rápido.
TIEMPO_MAXIMO = 0.001


@tool
def consultar_feriados(pais: str, anio: int) -> str:
    """Consulta los feriados nacionales de un país en un año.

    El país se pasa con su código de dos letras (PE para Perú, AR para
    Argentina, ES para España). Devuelve la fecha y el nombre de cada
    feriado.
    """
    url = f"https://date.nager.at/api/v3/PublicHolidays/{anio}/{pais}"
    respuesta = requests.get(url, timeout=TIEMPO_MAXIMO)
    feriados = [f"{f['date']} {f['localName']}" for f in respuesta.json()]
    return "\n".join(feriados)


# --- Baranda 1: datos personales --------------------------------------
pregunta = "Soy ana.perez@gmail.com. ¿Qué pide el punto 2 del assignment?"
resultado = agente_v2.invoke(
    {"messages": [{"role": "user", "content": pregunta}]},
    config={"run_name": "baranda-datos-personales", "tags": ["clase-4"]},
)
print("1. Datos personales")
print(f"   Lo que escribió el alumno: {pregunta}")
print(f"   Lo que vio el modelo:      {resultado['messages'][0].text}")
print()


# --- Baranda 2: una API caída -----------------------------------------
# El mismo agente con feriados de la clase 2, ahora con las barandas.
agente_con_feriados = create_agent(
    f"{PROVEEDOR}:{MODELO}",
    tools=[buscar_fecha, consultar_feriados],
    system_prompt="Sos el asistente del curso. Contestá en dos líneas.",
    middleware=BARANDAS,
)
pregunta = "¿Hay algún feriado en Perú antes de la entrega del assignment?"
resultado = agente_con_feriados.invoke(
    {"messages": [{"role": "user", "content": pregunta}]},
    config={"run_name": "baranda-api-caida", "tags": ["clase-4"]},
)
print("2. Una API caída (en la clase 2 esto terminaba en una excepción)")
print(f"   {pregunta}")
print(f"   {resultado['messages'][-1].text}")
print()


# --- Baranda 3: un tope de llamadas al modelo -------------------------
# Un tope de 1 a propósito: no le alcanza para usar una herramienta y
# después contestar. En la clase 2 esto era un GraphRecursionError.
agente_con_tope = create_agent(
    f"{PROVEEDOR}:{MODELO}",
    tools=[buscar_fecha],
    middleware=[ModelCallLimitMiddleware(run_limit=1, exit_behavior="end")],
)
pregunta = "¿Cuándo es el test 4?"
resultado = agente_con_tope.invoke(
    {"messages": [{"role": "user", "content": pregunta}]},
    config={"run_name": "baranda-tope-de-llamadas", "tags": ["clase-4"]},
)
print("3. Un tope de llamadas al modelo")
print(f"   {pregunta}")
print(f"   {resultado['messages'][-1].text}")
print()

wait_for_all_tracers()

print("Ninguna de las tres terminó en una excepción. En LangSmith, buscá las")
print("trazas «baranda-...»: en la de la API caída vas a ver los reintentos.")
