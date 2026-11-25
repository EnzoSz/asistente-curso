"""Paso 4: cerrar el ciclo. De producción, al examen.

Qué demuestra: la optimización continua es un ciclo, no un cambio
suelto. Las consultas que salieron mal en producción son las mejores
preguntas para el próximo examen: son reales y ya sabemos que cuestan.

Buscamos en el entorno production del agente las ejecuciones que el
alumno marcó como "no me sirvió" (el feedback le_sirvio = 0, el
pulgar abajo de la web) y copiamos sus preguntas a un dataset aparte, "para revisar".
Una persona les escribe la respuesta esperada y las pasa al dataset
principal. Desde ese día,
cada versión nueva del agente rinde también esas preguntas.

    producción -> feedback -> revisión -> dataset -> evaluación -> v3

Concepto del sílabo: optimización continua basada en evidencias de
producción (Módulo 3, Semana 4).

Cómo se ejecuta (necesita pulgares abajo en la web desplegada):
    uv run paso4_de_produccion_al_dataset.py
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone

import langsmith as ls
from dotenv import load_dotenv

load_dotenv()

AGENTE = os.getenv("LANGSMITH_AGENT_ID", "asistente-del-curso")
DATASET_REVISAR = "asistente-del-curso-para-revisar"


async def main():
    cliente = ls.Client()
    desde = datetime.now(timezone.utc) - timedelta(days=14)
    produccion = ls.agent_address(AGENTE, "production")
    destino = await cliente.sessions.resolve(**produccion)

    # --- 1. Las ejecuciones con feedback negativo ---------------------
    # El filtro se escribe en el lenguaje de consultas de LangSmith: "que
    # tengan feedback le_sirvio, y que su nota sea 0".
    malas = []
    async for run in cliente.runs.query(
        project_ids=[destino.session_id],
        is_root=True,
        min_start_time=desde,
        filter='and(eq(feedback_key, "le_sirvio"), eq(feedback_score, 0))',
        selects=["ID", "INPUTS"],
    ):
        malas.append(run)

    if not malas:
        print("No hay consultas marcadas como «no me sirvió» en production.")
        print("Entrá a la web desplegada, dejá pulgares abajo")
        print("y volvé a intentar.")
        return

    # --- 2. Sacar la pregunta de cada una -----------------------------
    # La pregunta es el último mensaje de la entrada de la ejecución.
    ejemplos = []
    for run in malas:
        mensaje = run.inputs["messages"][-1]
        pregunta = mensaje.get("content") or mensaje.get("kwargs", {}).get("content")
        ejemplos.append(
            {
                "inputs": {"pregunta": pregunta},
                "metadata": {"run_id": str(run.id), "origen": "produccion"},
            }
        )
        print(f"  No le sirvió: {pregunta}")
    print()

    # --- 3. Guardarlas en el dataset "para revisar" -------------------
    if not cliente.has_dataset(dataset_name=DATASET_REVISAR):
        cliente.create_dataset(
            DATASET_REVISAR,
            description="Consultas reales con feedback negativo, para revisar.",
        )
    cliente.create_examples(dataset_name=DATASET_REVISAR, examples=ejemplos)

    print(f"{len(ejemplos)} preguntas copiadas a «{DATASET_REVISAR}».")
    print("Ahora te toca a vos: en LangSmith, escribí la respuesta esperada de")
    print("cada una y pasala al dataset principal. El próximo examen las incluye.")


asyncio.run(main())
