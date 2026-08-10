"""Capa de vigencia normativa: mapea citas a normas derogadas.

El problema que resuelve no es que el corpus esté desactualizado, sino algo
más sutil: **un documento vigente puede citar una norma derogada**. La
Circular DDU 375 es de 2017, sigue publicada como vigente por el MINVU y su
doctrina se aplica, pero habla de la Ley 19.537, derogada en 2022. Descartar
el documento perdería doctrina aplicable; repetir su cita a ciegas produce
una respuesta que un revisor de la DOM descarta en el primer párrafo.

La salida correcta es mapear: conservar la doctrina, citar la norma vigente y
decir de dónde viene. Esta capa actúa en dos momentos —al armar el contexto y
al revisar la respuesta— y nunca lanza: si la tabla falta, el sistema
responde como antes en vez de caer.
"""

import json
import re
from functools import lru_cache
from pathlib import Path

from core.config import DATA_DIR

VIGENCIA_PATH = DATA_DIR / "vigencia.json"


@lru_cache(maxsize=1)
def _tabla():
    try:
        return json.loads(Path(VIGENCIA_PATH).read_text(encoding="utf-8"))
    except Exception:
        return {"derogadas": []}


def derogadas():
    return _tabla().get("derogadas", [])


def citadas_en(texto):
    """Normas derogadas que el texto invoca, en el orden de la tabla."""
    if not texto:
        return []
    return [d for d in derogadas() if re.search(d["patron"], texto)]


def anotacion(entrada):
    """Marca breve para el encabezado de un fragmento del contexto.

    Va junto a la fuente y no dentro del texto: el modelo debe ver que la
    doctrina sirve pero que la cita hay que trasladarla, sin que el aviso se
    confunda con el contenido del documento.
    """
    aviso = (
        f"ATENCIÓN: este fragmento cita la {entrada['norma']}, derogada el "
        f"{entrada['fecha_estado']} por la {entrada['reemplazada_por']}. "
        f"Su doctrina sigue siendo aplicable; la referencia legal debe "
        f"trasladarse a la {entrada['reemplazada_por']}."
    )
    # Las concordancias verificadas viajan con el aviso y no solo en la
    # corrección posterior: si el modelo puede nombrar el artículo equivalente
    # a la primera, no hace falta una segunda llamada.
    for c in concordancias_de(entrada):
        aviso += (
            f" El artículo {c['articulo']} de la {entrada['norma']} "
            f"({c['materia']}) corresponde a {c['equivalente']}."
        )
    return aviso


def concordancias_de(entrada):
    """Equivalencias artículo por artículo, cuando están verificadas."""
    return entrada.get("concordancias", [])


def referencias_sin_mapear(respuesta):
    """Normas derogadas citadas sin mencionar la que las reemplazó.

    Es la condición que obliga a reescribir: nombrar la Ley 19.537 no es un
    error si se advierte que fue reemplazada y de dónde viene la doctrina;
    lo es presentarla como norma aplicable sin más.
    """
    pendientes = []
    for entrada in citadas_en(respuesta):
        reemplazo = re.escape(entrada["reemplazada_por"]).replace(r"\ ", r"\s+")
        if not re.search(reemplazo, respuesta, re.IGNORECASE):
            pendientes.append(entrada)
    return pendientes


def instruccion_de_correccion(entradas):
    """Encargo de reescritura para el modelo, con las concordancias a mano."""
    partes = [
        "Tu respuesta anterior cita normas derogadas como si estuvieran "
        "vigentes. Reescríbela completa corrigiendo eso, sin cambiar nada más "
        "y sin mencionar que estás corrigiendo:"
    ]
    for e in entradas:
        detalle = (
            f"- La {e['norma']} ({e['nombre']}) fue derogada el "
            f"{e['fecha_estado']} por la {e['reemplazada_por']}, según el "
            f"{e['base_legal']}. Además, {e['regla_de_reenvio']}."
        )
        for c in concordancias_de(e):
            detalle += (
                f"\n  · El artículo {c['articulo']} de la {e['norma']} "
                f"({c['materia']}) corresponde a {c['equivalente']}."
            )
        partes.append(detalle)
    partes.append(
        "Cita la norma vigente como fuente de la regla. Cuando la doctrina "
        "provenga de una circular u otro documento que invoca la norma "
        "derogada, mantenla y atribúyesela, aclarando que su referencia legal "
        "se entiende hecha a la norma que la reemplazó. No descartes ese "
        "documento: sigue siendo aplicable."
    )
    return "\n".join(partes)
