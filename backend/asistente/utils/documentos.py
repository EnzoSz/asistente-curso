"""La base vectorial con los documentos del curso, guardada en SQLite.

La primera vez que arranca, parte los documentos en fragmentos, le pide a
Gemini un embedding por fragmento y los guarda en documentos.db. Las veces
siguientes los lee del archivo: Gemini solo recibe los fragmentos nuevos o
que cambiaron. Así, reiniciar el servidor no gasta llamadas de embeddings.

Usa SqliteStore, el almacén de LangGraph (el mismo paquete que guarda la
memoria de las conversaciones), con búsqueda semántica activada.
"""

import hashlib
import os
import sqlite3
import time

from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.store.base import PutOp
from langgraph.store.sqlite import SqliteStore

MODELO_EMBEDDINGS = "gemini-embedding-2"
DIMENSIONES = 768  # pedimos vectores de 768 (el modelo da hasta 3072)
ESPACIO = ("documentos",)  # la "carpeta" del almacén donde van los fragmentos

# backend/asistente/utils/documentos.py  ->  backend/documentos/
# y el archivo de la base queda al lado: backend/documentos.db
AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(AQUI, "..", "..", "documentos")
ARCHIVO_DB = os.path.join(AQUI, "..", "..", "documentos.db")

# gemini-embedding-2 busca mejor si el texto lleva un prefijo que dice qué
# es: un documento o una pregunta. SqliteStore usa la misma función para
# los dos casos, así que el prefijo lo ponemos nosotros: acá para los
# fragmentos y en tools.py (con prefijo_pregunta) para las búsquedas.
def prefijo_documento(fuente: str, texto: str) -> str:
    return f"title: {fuente} | text: {texto}"


def prefijo_pregunta(consulta: str) -> str:
    return f"task: search result | query: {consulta}"


# Leemos el .env acá mismo: este archivo se importa antes que el resto del
# agente, y los embeddings necesitan GOOGLE_API_KEY desde el primer momento.
load_dotenv()

# El plan gratuito de Gemini tiene límite de pedidos por minuto (429) y a
# veces el servicio está saturado (503). Son errores pasajeros: esperamos
# un poco y reintentamos, en vez de tumbar toda la respuesta del agente.
ERRORES_PASAJEROS = ("429", "500", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE")
INTENTOS = 4


def con_reintentos(funcion, *args):
    for intento in range(INTENTOS):
        try:
            return funcion(*args)
        except Exception as error:
            pasajero = any(codigo in str(error) for codigo in ERRORES_PASAJEROS)
            if not pasajero or intento == INTENTOS - 1:
                raise
            time.sleep(2 ** (intento + 1))  # 2s, 4s, 8s


class EmbeddingsConReintentos(GoogleGenerativeAIEmbeddings):
    def embed_documents(self, texts, **kwargs):
        return con_reintentos(super().embed_documents, texts)

    def embed_query(self, text, **kwargs):
        return con_reintentos(super().embed_query, text)


embeddings = EmbeddingsConReintentos(
    model=MODELO_EMBEDDINGS, output_dimensionality=DIMENSIONES
)

# check_same_thread=False: FastAPI atiende cada pedido en un hilo distinto.
conexion = sqlite3.connect(
    ARCHIVO_DB, check_same_thread=False, isolation_level=None
)
base = SqliteStore(
    conexion,
    # Se indexa "indexado" (el texto con su prefijo); "texto" es lo que lee el agente.
    index={"dims": DIMENSIONES, "embed": embeddings, "fields": ["indexado"]},
)
base.setup()  # crea las tablas si no existen

# 1. Partir los documentos en fragmentos. Cada fragmento se identifica por
#    su contenido: si el texto cambia, cambia la clave.
partidor = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
fragmentos = {}
for nombre in sorted(os.listdir(CARPETA)):
    with open(os.path.join(CARPETA, nombre), encoding="utf-8") as archivo:
        texto = archivo.read()
    for parte in partidor.split_text(texto):
        clave = hashlib.sha256(f"{nombre}|{parte}".encode()).hexdigest()[:16]
        fragmentos[clave] = {
            "texto": parte,
            "fuente": nombre,
            "indexado": prefijo_documento(nombre, parte),
        }

# 2. Ver qué hay guardado (leer no llama a Gemini: no hay consulta).
guardados = {item.key for item in base.search(ESPACIO, limit=10_000)}

# 3. Guardar solo lo nuevo, en un solo pedido de embeddings, y borrar lo que
#    ya no está en los documentos.
operaciones = [
    PutOp(ESPACIO, clave, valor)
    for clave, valor in fragmentos.items()
    if clave not in guardados
]
operaciones += [PutOp(ESPACIO, clave, None) for clave in guardados - fragmentos.keys()]
if operaciones:
    base.batch(operaciones)

nuevos = len(fragmentos.keys() - guardados)
print(f"Documentos: {len(fragmentos)} fragmentos en documentos.db ({nuevos} nuevos)")
