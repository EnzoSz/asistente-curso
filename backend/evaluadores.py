"""Los evaluadores del asistente: cómo se corrige el examen.

Qué es: igual que el paquete asistente/, este archivo no se ejecuta
solo. Lo importan los pasos 2 y 3. Tiene dos cosas:

    1. responder: la función que le toma el examen al agente. Recibe
       un ejemplo del dataset, le hace la pregunta al asistente y
       devuelve lo que contestó y qué herramientas usó.
    2. Cuatro evaluadores de código. Cada uno es un criterio de
       evaluación: recibe la respuesta (y la referencia) y devuelve
       True o False. LangSmith calcula el promedio de cada uno.

Las funciones son el contenido de la clase: cada evaluador es un
criterio que se puede explicar en una línea, y eso es lo que pide el
punto 4 del assignment.

Concepto del sílabo: evaluadores, datasets y feedback para el monitoreo
continuo de la calidad (Módulo 3, Semana 3).
"""

from asistente.agent import agente

# Las frases con las que el asistente admite que no encontró algo.
FRASES_DE_NO_SE = [
    "no lo encontr",
    "no encontr",
    "no está en",
    "no figura",
    "no tengo",
]


# --- La función que rinde el examen ---------------------------------
def responder(inputs: dict) -> dict:
    """Le hace al asistente la pregunta de un ejemplo del dataset."""
    resultado = agente.invoke(
        {"messages": [{"role": "user", "content": inputs["pregunta"]}]}
    )

    herramientas = []
    for mensaje in resultado["messages"]:
        if mensaje.type == "ai":
            for llamada in mensaje.tool_calls:
                herramientas.append(llamada["name"])

    return {"respuesta": resultado["messages"][-1].text, "herramientas": herramientas}


# --- Criterio 1: ¿usó la herramienta que correspondía? -----------------
def herramienta_correcta(outputs: dict, reference_outputs: dict) -> bool:
    """Fechas: el calendario. Todo lo demás: buscar en los documentos.
    Incluso para las trampas: tiene que buscar antes de decir que no sabe."""
    if reference_outputs["fuente"] == "calendario":
        return "buscar_fecha" in outputs["herramientas"]
    return "buscar_en_documentos" in outputs["herramientas"]


# --- Criterio 2: ¿citó el documento correcto? ------------------------
def cita_la_fuente(outputs: dict, reference_outputs: dict) -> bool:
    """Si la respuesta sale de un documento, tiene que nombrarlo."""
    fuente = reference_outputs["fuente"]
    if fuente in ("calendario", "ninguna"):
        return True  # no hay documento que citar
    return fuente in outputs["respuesta"]


# --- Criterio 3: ¿es honesto? -----------------------------------------
def honestidad(outputs: dict, reference_outputs: dict) -> bool:
    """Si la respuesta no existe, tiene que decir que no la encontró.
    Si existe, no tiene que rendirse diciendo que no la encontró."""
    texto = outputs["respuesta"].lower()
    dice_no_se = any(frase in texto for frase in FRASES_DE_NO_SE)
    if reference_outputs["fuente"] == "ninguna":
        return dice_no_se
    return not dice_no_se


# --- Criterio 4: ¿respeta el formato? ---------------------------------
def es_breve(outputs: dict) -> bool:
    """El system_prompt pide tres líneas como máximo."""
    lineas = [linea for linea in outputs["respuesta"].splitlines() if linea.strip()]
    return len(lineas) <= 3
