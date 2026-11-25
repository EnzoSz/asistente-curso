"""Paso 2: ¿la v2 es mejor? Las dos versiones rinden el mismo examen.

Qué demuestra: optimizar no es cambiar el prompt porque "parece mejor".
Es cambiar algo, medirlo contra lo que había y decidir con números.
Las dos versiones del asistente rinden el examen de la clase 3 (el mismo
dataset, los mismos cuatro evaluadores) y comparamos criterio por
criterio, más la latencia.

Si la v2 gana en calidad sin empeorar demasiado en tiempo, se publica.
Si no, se queda la v1. Esa decisión, con su evidencia, es el punto 6
del assignment.

Concepto del sílabo: optimización continua a partir de trazas y
métricas de producción (Módulo 3, Semana 4).

Cómo se ejecuta (necesita el dataset de la clase 3, parado en backend/):
    uv run paso2_comparar_versiones.py

Si la v2 gana, se publica: en Render, VERSION_AGENTE=v2.
"""

from langsmith import Client

from asistente.agent import MODELO, agente_v2
from evaluadores import (
    cita_la_fuente,
    es_breve,
    herramienta_correcta,
    honestidad,
    responder,
)

DATASET = "asistente-del-curso-preguntas"
CRITERIOS = [herramienta_correcta, cita_la_fuente, honestidad, es_breve]


# responder (de evaluadores.py) le toma el examen a la v1. Esta es la
# misma función, pero para la v2.
def responder_v2(inputs: dict) -> dict:
    resultado = agente_v2.invoke(
        {"messages": [{"role": "user", "content": inputs["pregunta"]}]}
    )
    herramientas = []
    for mensaje in resultado["messages"]:
        if mensaje.type == "ai":
            for llamada in mensaje.tool_calls:
                herramientas.append(llamada["name"])
    return {"respuesta": resultado["messages"][-1].text, "herramientas": herramientas}


cliente = Client()


# --- 1. La v1 rinde el examen -----------------------------------------
print("Evaluando la v1...")
resultados_v1 = cliente.evaluate(
    responder,
    data=DATASET,
    evaluators=CRITERIOS,
    experiment_prefix="v1-produccion",
    metadata={"modelo": MODELO, "version": "v1"},
    max_concurrency=2,
)


# --- 2. La v2 rinde el mismo examen -----------------------------------
print("Evaluando la v2...")
resultados_v2 = cliente.evaluate(
    responder_v2,
    data=DATASET,
    evaluators=CRITERIOS,
    experiment_prefix="v2-candidata",
    metadata={"modelo": MODELO, "version": "v2"},
    max_concurrency=2,
)


# --- 3. Sumar las notas y los tiempos de cada versión -----------------
# Lo escribimos dos veces, una por versión: se lee mejor que un bucle.
cantidad = 0
notas_v1 = {}
segundos_v1 = 0
for fila in resultados_v1:
    cantidad += 1
    segundos_v1 += fila["run"].latency or 0
    for evaluacion in fila["evaluation_results"]["results"]:
        nota = evaluacion.score or 0
        notas_v1[evaluacion.key] = notas_v1.get(evaluacion.key, 0) + nota

notas_v2 = {}
segundos_v2 = 0
for fila in resultados_v2:
    segundos_v2 += fila["run"].latency or 0
    for evaluacion in fila["evaluation_results"]["results"]:
        nota = evaluacion.score or 0
        notas_v2[evaluacion.key] = notas_v2.get(evaluacion.key, 0) + nota


# --- 4. La comparación -------------------------------------------------
print()
print(f"  {'criterio':<22}{'v1':>8}{'v2':>8}")
for criterio in notas_v1:
    v1 = notas_v1[criterio] / cantidad
    v2 = notas_v2.get(criterio, 0) / cantidad
    marca = "  <- mejora" if v2 > v1 else ("  <- empeora" if v2 < v1 else "")
    print(f"  {criterio:<22}{v1:>8.0%}{v2:>8.0%}{marca}")
print(f"  {'segundos por pregunta':<22}{segundos_v1 / cantidad:>8.1f}"
      f"{segundos_v2 / cantidad:>8.1f}")
print()
print(f"Experimentos: {resultados_v1.experiment_name}")
print(f"              {resultados_v2.experiment_name}")
print("En LangSmith, seleccioná los dos y tocá «Compare»: ahí ves también los")
print("tokens y, pregunta por pregunta, qué cambió.")
