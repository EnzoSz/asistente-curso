"""Las herramientas del asistente: el calendario y la búsqueda en documentos.

Son las mismas de las clases anteriores. Lo único que cambió es dónde
viven: en su propio archivo, como pide la estructura de LangGraph.
"""

from datetime import date

from langchain.tools import tool

from asistente.utils.documentos import ESPACIO, base

# El calendario del Módulo 3. Son fechas de ejemplo: cambialas por las de
# tu cohorte para que las respuestas tengan sentido.
FECHAS = {
    "clase 1": "2026-11-11",
    "test 1": "2026-11-15",
    "clase 2": "2026-11-18",
    "test 2": "2026-11-22",
    "clase 3": "2026-11-25",
    "test 3": "2026-11-29",
    "clase 4": "2026-12-02",
    "test 4": "2026-12-06",
    "assignment": "2026-12-13",
}


@tool
def buscar_fecha(evento: str) -> str:
    """Busca en el calendario del curso la fecha de un evento.

    El evento se pasa por su nombre, por ejemplo "test 1", "clase 3" o
    "assignment". Devuelve la fecha en formato AAAA-MM-DD. Usala cada vez
    que necesites saber cuándo es algo del curso.
    """
    for nombre, fecha in FECHAS.items():
        if nombre in evento.lower():
            return f"{nombre}: {fecha}"
    return f"No encontré '{evento}' en el calendario del curso."


@tool
def contar_dias(fecha: str) -> str:
    """Cuenta cuántos días faltan desde hoy hasta una fecha.

    La fecha se pasa en formato AAAA-MM-DD, por ejemplo "2026-12-13".
    Usala cuando te pregunten cuánto falta para algo y ya sepas la fecha.
    """
    try:
        dias = (date.fromisoformat(fecha) - date.today()).days
    except ValueError:
        return f"'{fecha}' no es una fecha válida. Usá el formato AAAA-MM-DD."
    return f"Faltan {dias} días para el {fecha}."


@tool
def buscar_en_documentos(consulta: str) -> str:
    """Busca en los documentos oficiales del curso: el sílabo del
    Módulo 3, la guía del assignment y las preguntas frecuentes.

    La consulta se escribe en lenguaje natural, por ejemplo "qué pide el
    punto 3 del assignment". Devuelve los tres fragmentos más relevantes,
    cada uno con el nombre del archivo de donde salió. Usala para
    cualquier duda sobre contenidos, evaluación o funcionamiento del curso.
    """
    resultados = base.search(ESPACIO, query=consulta, limit=3)

    bloques = []
    for fragmento in resultados:
        bloques.append(f"[{fragmento.value['fuente']}]\n{fragmento.value['texto']}")
    return "\n\n".join(bloques)


# La lista que usa agent.py. Si sumás una herramienta, agregala acá.
HERRAMIENTAS = [buscar_fecha, contar_dias, buscar_en_documentos]
