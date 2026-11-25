"""Paso 0: verificar que el backend está listo para la nube y para la práctica.

Qué demuestra: un diagnóstico del entorno de trabajo. Comprueba la versión
de Python, que las librerías estén instaladas, que exista el .env con las
claves (Anthropic, Google y LangSmith) y la configuración de las trazas, que
esté git (para subir el proyecto a GitHub), y hace una llamada de prueba a
cada servicio, incluido el modelo de respaldo de la v2.

Concepto del sílabo: optimización continua a partir de trazas y
métricas de producción (Módulo 3, Semana 4).

Cómo se ejecuta:
    uv run paso0_verificar_entorno.py

Este script es el semáforo verde de la clase: si todo sale OK, el resto
de los pasos va a funcionar. Está hecho para no romperse nunca: si algo
falta lo anota como FALTA y sigue con el resto de los chequeos.
"""

import os
import re
import sys
from importlib.metadata import version

# Acá vamos anotando cada resultado para mostrar el resumen al final.
resumen = []

print("Verificación del backend - Módulo 3, Clase 4")
print()


# --- 1. Versión de Python ------------------------------------------
actual = sys.version_info
if actual >= (3, 11):
    print(f"[OK]    Python {actual.major}.{actual.minor}.{actual.micro}")
    resumen.append("[OK]    Python 3.11 o superior")
else:
    print(f"[FALTA] Python {actual.major}.{actual.minor}: hace falta 3.11 o más")
    resumen.append("[FALTA] Python 3.11 o superior")


# --- 2. Librerías instaladas ---------------------------------------
# Pares (nombre del paquete en PyPI, módulo que se importa en el código).
# Nuevas: fastapi (la API) y langgraph-checkpoint-sqlite (la memoria y la
# base vectorial, las dos en archivos SQLite).
# langsmith guarda los datasets y los resultados de las evaluaciones.
librerias = [
    ("fastapi", "fastapi"),
    ("langgraph-checkpoint-sqlite", "langgraph.checkpoint.sqlite"),
    ("langchain", "langchain"),
    ("langchain-core", "langchain_core"),
    ("langchain-anthropic", "langchain_anthropic"),
    ("langchain-google-genai", "langchain_google_genai"),
    ("langchain-text-splitters", "langchain_text_splitters"),
    ("langgraph", "langgraph"),
    ("langsmith", "langsmith"),
    ("numpy", "numpy"),
    ("python-dotenv", "dotenv"),
    ("requests", "requests"),
]
for paquete, modulo in librerias:
    try:
        __import__(modulo)
        print(f"[OK]    {paquete} {version(paquete)}")
        resumen.append(f"[OK]    {paquete}")
    except Exception:
        # Si esto falla, casi siempre es porque faltó ejecutar "uv sync".
        print(f"[FALTA] {paquete}: no se pudo importar. Corré: uv sync")
        resumen.append(f"[FALTA] {paquete}")


# La base vectorial usa sqlite-vec, una extensión de SQLite. Algunos Python
# no permiten cargar extensiones: el de uv sí.
try:
    import sqlite3

    import sqlite_vec

    prueba = sqlite3.connect(":memory:")
    prueba.enable_load_extension(True)
    sqlite_vec.load(prueba)
    vec = prueba.execute("select vec_version()").fetchone()[0]
    print(f"[OK]    SQLite con búsqueda vectorial (sqlite-vec {vec})")
    resumen.append("[OK]    sqlite-vec")
except Exception:
    print("[FALTA] tu Python no carga extensiones de SQLite: usá el de uv")
    print("        (uv python install 3.12, y después uv sync)")
    resumen.append("[FALTA] sqlite-vec")


# --- 3. Archivo .env y carpeta ---------------------------------------
if os.path.isfile(".env"):
    print("[OK]    archivo .env encontrado")
    resumen.append("[OK]    archivo .env")
else:
    print("[FALTA] archivo .env: copiá .env.example a .env y pegá tus claves")
    resumen.append("[FALTA] archivo .env")

# Tenés que estar parado en backend/: ahí están la API y el agente.
if os.path.isfile(os.path.join("api", "main.py")):
    print("[OK]    estás en la carpeta backend/")
    resumen.append("[OK]    carpeta backend/")
else:
    print("[FALTA] parate en practica-clase-04/backend (cd backend)")
    resumen.append("[FALTA] carpeta backend/")

# NUEVO: git, para subir el proyecto a GitHub (Render y Streamlit
# despliegan desde un repositorio).
try:
    import subprocess

    salida = subprocess.run(["git", "--version"], capture_output=True, text=True)
    print(f"[OK]    {salida.stdout.strip()}")
    resumen.append("[OK]    git")
except Exception:
    print("[FALTA] git no está instalado: bajalo de git-scm.com")
    resumen.append("[FALTA] git")


# --- 4. Las dos claves ---------------------------------------------
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    print("[FALTA] no se pudo leer el .env, se usan variables del sistema")

# Por seguridad mostramos solo los últimos 4 caracteres de cada clave:
# así podés pegar esta salida en el chat del curso sin revelarlas.
clave = os.getenv("ANTHROPIC_API_KEY", "").strip()
if clave.startswith("sk-ant-"):
    print(f"[OK]    ANTHROPIC_API_KEY cargada, termina en ...{clave[-4:]}")
    resumen.append("[OK]    ANTHROPIC_API_KEY")
else:
    print("[FALTA] ANTHROPIC_API_KEY: falta, o no empieza con 'sk-ant-'")
    resumen.append("[FALTA] ANTHROPIC_API_KEY")

clave_google = os.getenv("GOOGLE_API_KEY", "").strip()
if clave_google:
    print(f"[OK]    GOOGLE_API_KEY cargada, termina en ...{clave_google[-4:]}")
    resumen.append("[OK]    GOOGLE_API_KEY")
else:
    print("[FALTA] GOOGLE_API_KEY: creala en aistudio.google.com")
    resumen.append("[FALTA] GOOGLE_API_KEY")

clave_ls = os.getenv("LANGSMITH_API_KEY", "").strip()
if clave_ls.startswith("lsv2_"):
    print(f"[OK]    LANGSMITH_API_KEY cargada, termina en ...{clave_ls[-4:]}")
    resumen.append("[OK]    LANGSMITH_API_KEY")
elif clave_ls:
    print("[FALTA] LANGSMITH_API_KEY no empieza con 'lsv2_': revisá que sea la de LangSmith")
    resumen.append("[FALTA] LANGSMITH_API_KEY")
else:
    print("[FALTA] LANGSMITH_API_KEY: creala en smith.langchain.com > Settings > API Keys")
    resumen.append("[FALTA] LANGSMITH_API_KEY")


# --- 5. La configuración de las trazas -----------------------------
# Las dos líneas que prenden la observabilidad. Son lo único nuevo del
# .env de hoy.
if os.getenv("LANGSMITH_TRACING", "").strip().lower() == "true":
    print("[OK]    LANGSMITH_TRACING=true: las ejecuciones se envían a LangSmith")
    resumen.append("[OK]    LANGSMITH_TRACING")
else:
    print("[FALTA] LANGSMITH_TRACING: poné LANGSMITH_TRACING=true en el .env")
    resumen.append("[FALTA] LANGSMITH_TRACING")

# Adónde van las trazas: un agente y un entorno. Son las reglas de
# LangSmith para el identificador: minúsculas, números y guiones,
# empieza con letra y termina con letra o número.
agente_id = os.getenv("LANGSMITH_AGENT_ID", "").strip()
if re.fullmatch(r"[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?", agente_id):
    print(f"[OK]    LANGSMITH_AGENT_ID={agente_id}")
    resumen.append("[OK]    LANGSMITH_AGENT_ID")
elif agente_id:
    print(f"[FALTA] LANGSMITH_AGENT_ID={agente_id}: solo minúsculas, números y guiones")
    resumen.append("[FALTA] LANGSMITH_AGENT_ID")
else:
    print("[FALTA] LANGSMITH_AGENT_ID: poné LANGSMITH_AGENT_ID=asistente-del-curso")
    resumen.append("[FALTA] LANGSMITH_AGENT_ID")

entorno = os.getenv("LANGSMITH_AGENT_ENVIRONMENT", "").strip().lower()
if entorno in ("local", "development", "staging", "production"):
    print(f"[OK]    LANGSMITH_AGENT_ENVIRONMENT={entorno}")
    resumen.append("[OK]    LANGSMITH_AGENT_ENVIRONMENT")
else:
    print("[FALTA] LANGSMITH_AGENT_ENVIRONMENT: poné LANGSMITH_AGENT_ENVIRONMENT=local")
    resumen.append("[FALTA] LANGSMITH_AGENT_ENVIRONMENT")

# La forma vieja (por proyecto) no se puede mezclar con la nueva.
if os.getenv("LANGSMITH_PROJECT"):
    print("[FALTA] sobra LANGSMITH_PROJECT: borrala del .env (es la forma vieja)")
    resumen.append("[FALTA] sin LANGSMITH_PROJECT")


# NUEVO: qué versión del agente atiende la API (v1 o v2).
version_agente = os.getenv("VERSION_AGENTE", "v1").strip()
if version_agente in ("v1", "v2"):
    print(f"[OK]    VERSION_AGENTE={version_agente}")
    resumen.append("[OK]    VERSION_AGENTE")
else:
    print(f"[FALTA] VERSION_AGENTE={version_agente}: tiene que ser v1 o v2")
    resumen.append("[FALTA] VERSION_AGENTE")


# --- 6. Una llamada de prueba a cada modelo -----------------------
# Los mismos de asistente/agent.py y asistente/utils/documentos.py.
MODELOS_DE_CHAT = [
    ("anthropic:claude-sonnet-5-5", "el que contesta"),
    ("google_genai:gemini-3.8-flash", "el respaldo de la v2"),
]
for modelo, papel in MODELOS_DE_CHAT:
    try:
        from langchain.chat_models import init_chat_model

        init_chat_model(modelo).invoke("Decí hola.")
        print(f"[OK]    {modelo} respondió ({papel})")
        resumen.append(f"[OK]    {modelo}")
    except Exception as error:
        print(f"[FALTA] {modelo} ({papel}): {type(error).__name__}: {str(error)[:120]}")
        resumen.append(f"[FALTA] {modelo}")

try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    vector = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2", output_dimensionality=768
    ).embed_query("hola")
    print(f"[OK]    gemini-embedding-2 respondió ({len(vector)} dimensiones)")
    resumen.append("[OK]    modelo de embeddings")
except Exception as error:
    print(f"[FALTA] gemini-embedding-2: {type(error).__name__}: {str(error)[:120]}")
    resumen.append("[FALTA] modelo de embeddings")


# --- 7. Una llamada de prueba a LangSmith --------------------------
# Le pedimos a LangSmith la lista de proyectos (solo uno). Si responde
# 200, la clave sirve. Si tu cuenta está en la región de Europa, poné en
# el .env LANGSMITH_ENDPOINT=https://eu.api.smith.langchain.com
URL_LANGSMITH = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

if not clave_ls:
    print("[FALTA] LangSmith: se omite, no hay clave para probar")
    resumen.append("[FALTA] conexión con LangSmith")
else:
    try:
        import requests

        r = requests.get(
            f"{URL_LANGSMITH}/sessions",
            headers={"x-api-key": clave_ls},
            params={"limit": 1},
            timeout=30,
        )
        if r.status_code == 200:
            print("[OK]    LangSmith respondió: la clave funciona")
            resumen.append("[OK]    conexión con LangSmith")
        elif r.status_code in (401, 403):
            print(f"[FALTA] clave de LangSmith inválida ({r.status_code})")
            resumen.append("[FALTA] conexión con LangSmith")
        else:
            print(f"[FALTA] LangSmith respondió {r.status_code}")
            resumen.append("[FALTA] conexión con LangSmith")
    except Exception as error:
        print(f"[FALTA] LangSmith: no hubo conexión ({type(error).__name__})")
        resumen.append("[FALTA] conexión con LangSmith")


# --- Resumen final -------------------------------------------------
print()
print("Resumen:")
for linea in resumen:
    print(f"  {linea}")

print()
if all(linea.startswith("[OK]") for linea in resumen):
    print("Semáforo verde: tu entorno está listo.")
    print("Siguiente paso: uv run fastapi dev api/main.py")
else:
    print("Resolvé lo que aparece como FALTA antes de seguir.")
    print("Mirá la sección '¿Y si algo falla?' del README.md.")
