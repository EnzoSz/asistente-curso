"""Paso 1: las métricas de producción del asistente.

Qué demuestra: desde el bloque 1, el asistente atiende en la web de
verdad, y sus trazas van al entorno production. Leemos las ejecuciones
de los últimos 7 días de ese entorno y calculamos lo que mira un equipo
de operaciones:

    - Volumen: cuántas consultas atendió
    - Errores: qué porcentaje falló
    - Latencia: cuánto tardó la mitad de las consultas (p50) y cuánto
      la peor de cada veinte (p95)
    - Tokens y costo: cuánto consume una consulta típica
    - Calidad: el promedio del feedback que guardamos en la clase 3
    - Herramientas: cuáles usa más

Son las métricas del punto 5 del assignment, y lo mismo que muestra el
dashboard del entorno en LangSmith. Acá las calculamos a mano para
saber de dónde sale cada número.

Como en el paso 3 de la clase 2, las funciones de lectura de LangSmith
son asíncronas: el trabajo está dentro de async def main().

Concepto del sílabo: dashboards, costos, errores y desempeño del agente
en contextos de negocio (Módulo 3, Semana 4).

Cómo se ejecuta:
    uv run paso1_metricas_de_produccion.py
"""

import asyncio
import os
from datetime import datetime, timedelta, timezone

import langsmith as ls
from dotenv import load_dotenv

load_dotenv()

AGENTE = os.getenv("LANGSMITH_AGENT_ID", "asistente-del-curso")

# Qué entorno medimos. "production" es la web desplegada en Render (y la
# web de la clase 3). Tus pruebas en tu computadora están en "local".
ENTORNO = "production"
DIAS = 7

# Precio de referencia, en dólares por millón de tokens. Revisá el precio
# actual de Claude Sonnet en anthropic.com/pricing y cambialo acá.
PRECIO_ENTRADA = 0.10
PRECIO_SALIDA = 0.40


async def main():
    cliente = ls.Client()
    desde = datetime.now(timezone.utc) - timedelta(days=DIAS)
    destino = await cliente.sessions.resolve(**ls.agent_address(AGENTE, ENTORNO))

    # --- 1. Las ejecuciones completas de la última semana ------------
    ejecuciones = []
    async for run in cliente.runs.query(
        project_ids=[destino.session_id],
        is_root=True, # Solo las ejecuciones raíz (no las subherramientas)
        min_start_time=desde,
        selects=["STATUS", "LATENCY_SECONDS", "PROMPT_TOKENS",
                 "COMPLETION_TOKENS", "FEEDBACK_STATS"],
        include_subtree_usage=True, # Incluye el uso de subprocesos (herramientas) en las métricas
    ):
        ejecuciones.append(run)

    if not ejecuciones:
        print(f"No hay ejecuciones en «{AGENTE}» ({ENTORNO}) en {DIAS} días.")
        print("Usá la web desplegada (o la de la clase 3), o cambiá ENTORNO.")
        return

    total = len(ejecuciones)
    errores = 0
    latencias = []
    tokens_entrada = 0
    tokens_salida = 0
    for run in ejecuciones:
        if run.status == "ERROR":
            errores += 1
        latencias.append(run.latency_seconds or 0)
        tokens_entrada += run.prompt_tokens or 0
        tokens_salida += run.completion_tokens or 0

    # Percentiles: ordenamos las latencias y miramos la que está en la
    # mitad (p50) y la que está al 95 % de la lista (p95).
    latencias.sort() # Ordenamos las latencias para calcular percentiles
    p50 = latencias[int(total * 0.50)] # Percentil 50 (mediana)
    p95 = latencias[min(int(total * 0.95), total - 1)] # Percentil 95

    costo = tokens_entrada * PRECIO_ENTRADA + tokens_salida * PRECIO_SALIDA
    costo = costo / 1_000_000  # los precios son por millón de tokens

    # --- 2. El feedback de calidad -----------------------------------
    # Cada ejecución trae un resumen de sus notas: {"le_sirvio": ...}
    notas = {}
    for run in ejecuciones:
        for clave, datos in (run.feedback_stats or {}).items():
            if datos.avg is not None:
                notas.setdefault(clave, []).append(datos.avg)

    # --- 3. Qué herramientas se usan ---------------------------------
    usos = {}
    async for run in cliente.runs.query(
        project_ids=[destino.session_id],
        run_type="TOOL",
        min_start_time=desde,
        selects=["NAME"], # Solo necesitamos el nombre de la herramienta usada
    ):
        usos[run.name] = usos.get(run.name, 0) + 1

    # --- 4. El tablero, en texto -------------------------------------
    print(f"Agente «{AGENTE}», entorno {ENTORNO}, últimos {DIAS} días")
    print()
    print("DESEMPEÑO")
    print(f"  Consultas atendidas      {total}")
    print(f"  Latencia p50             {p50:.1f} s")
    print(f"  Latencia p95             {p95:.1f} s")
    print()
    print("ERRORES")
    print(f"  Ejecuciones con error    {errores} ({errores / total:.0%})")
    print()
    print("COSTOS (precio de referencia)")
    print(f"  Tokens por consulta      {(tokens_entrada + tokens_salida) // total}")
    print(f"  Costo total              USD {costo:.4f}")
    print(f"  Costo por 1000 consultas USD {costo / total * 1000:.2f}")
    print()
    print("CALIDAD (feedback)")
    if not notas:
        print("  Sin feedback en este entorno: dejá pulgares en la web")
    for clave, valores in notas.items():
        promedio = sum(valores) / len(valores)
        print(f"  {clave:<24} {promedio:.0%}  ({len(valores)} notas)")
    print()
    print("HERRAMIENTAS")
    for nombre, cantidad in sorted(usos.items(), key=lambda par: -par[1]):
        print(f"  {nombre:<24} {cantidad}")


asyncio.run(main())
