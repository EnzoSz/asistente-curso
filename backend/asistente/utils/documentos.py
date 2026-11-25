"""La base vectorial con los documentos del curso, guardada en SQLite.

La primera vez que arranca, parte los documentos en fragmentos, le pide a
NVIDIA un embedding por fragmento y los guarda en documentos.db. Las veces
siguientes los lee del archivo: NVIDIA solo recibe los fragmentos nuevos o
que cambiaron. Así, reiniciar el servidor no gasta llamadas de embeddings.

Usa SqliteStore, el almacén de LangGraph (el mismo paquete que guarda la
memoria de las conversaciones), con búsqueda semántica activada.
"""

import hashlib
import os
import sqlite3
import warnings

from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.store.base import PutOp
from langgraph.store.sqlite import SqliteStore

MODELO_EMBEDDINGS = "nvidia/nemotron-3.5-embed-1b"
DIMENSIONES = 2048  # el tamaño del vector que devuelve ese modelo
ESPACIO = ("documentos",)  # la "carpeta" del almacén donde van los fragmentos

# backend/asistente/utils/documentos.py  ->  backend/documentos/
# y el archivo de la base queda al lado: backend/documentos.db
AQUI = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(AQUI, "..", "..", "documentos")
ARCHIVO_DB = os.path.join(AQUI, "..", "..", "documentos.db")

# Nemotron 3.5 Embed es tan nuevo que el conector todavía avisa que
# "puede fallar". Funciona igual: callamos ese aviso.
warnings.filterwarnings("ignore", message=".*inference may fail")

# Leemos el .env acá mismo: este archivo se importa antes que el resto del
# agente, y los embeddings necesitan NVIDIA_API_KEY desde el primer momento.
load_dotenv()
embeddings = NVIDIAEmbeddings(model=MODELO_EMBEDDINGS, truncate="END")

# check_same_thread=False: FastAPI atiende cada pedido en un hilo distinto.
conexion = sqlite3.connect(
    ARCHIVO_DB, check_same_thread=False, isolation_level=None
)
base = SqliteStore(
    conexion,
    index={"dims": DIMENSIONES, "embed": embeddings, "fields": ["texto"]},
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
        fragmentos[clave] = {"texto": parte, "fuente": nombre}

# 2. Ver qué hay guardado (leer no llama a NVIDIA: no hay consulta).
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
