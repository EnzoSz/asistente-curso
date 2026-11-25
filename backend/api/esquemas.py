"""Qué entra y qué sale de la API.

Con Pydantic describimos la forma de cada pedido y de cada respuesta.
FastAPI usa estas clases para tres cosas:
    1. Rechazar pedidos mal armados (con un error 422 que explica qué falta).
    2. Convertir el JSON que llega en un objeto de Python.
    3. Armar la documentación de /docs sola.
"""

from pydantic import BaseModel, Field


class Pregunta(BaseModel):
    """Lo que manda el front cuando el alumno escribe algo."""

    pregunta: str = Field(min_length=1, max_length=1000)
    hilo_id: str = Field(description="Identifica la conversación (como thread_id)")
    alumno: str = Field(default="anonimo", description="Quién pregunta")


class Respuesta(BaseModel):
    """Lo que devuelve la API."""

    respuesta: str
    hilo_id: str
    run_id: str = Field(description="El id de la traza: sirve para el feedback")
    herramientas: list[str]


class Opinion(BaseModel):
    """El pulgar arriba o abajo del alumno sobre una respuesta."""

    run_id: str
    le_sirvio: bool
    comentario: str = ""
