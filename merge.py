import requests
import hashlib
import re
from collections import Counter

# ---------------------------------------------------------------------------
# FUENTE (única)
# ---------------------------------------------------------------------------

URL = "https://pastebin.com/raw/hV2z2e9g"

EPG_URL = "http://143.47.50.252:5000/getEPG"

# Solo se conservan los canales cuyo group-title ORIGINAL (sin importar
# mayúsculas/minúsculas) esté en esta lista. El resto se descarta.
CATEGORIAS = {
    "movistar deportes fairplay",
    "dazn hls",
    "movistar deportes playready",
    "dazn",
}

# Grupos que aparecerán los primeros en la app (se les añade el prefijo).
GRUPOS_PRIORITARIOS = {
    "movistar deportes fairplay",
}
PREFIJO_GRUPO_PRIORITARIO = "00 ⭐ "

# Si lo pones en True se aplicarán también las BLOCK_WORDS.
APLICAR_BLOCK_WORDS = False

BLOCK_WORDS = [
    "portugal",
    "polsat",
    "israel",
    # ... pega aquí el resto de tu lista si activas APLICAR_BLOCK_WORDS ...
]

contador = Counter()


# ---------------------------------------------------------------------------
# UTILIDADES
# ---------------------------------------------------------------------------

def _quitar_urls_de_atributos(extinf):
    texto = re.sub(r'tvg-logo="[^"]*"', "", extinf, flags=re.IGNORECASE)
    texto = re.sub(r'catchup-source="[^"]*"', "", texto, flags=re.IGNORECASE)
    return texto


def _patron_para_palabra(palabra):
    prefijo = r"\b" if palabra[0].isalnum() else ""
    sufijo = r"\b" if palabra[-1].isalnum() else ""
    return prefijo + re.escape(palabra) + sufijo


_palabras = sorted(
    {p.strip().casefold() for p in BLOCK_WORDS if p.strip()},
    key=len,
    reverse=True,
)

if _palabras:
    PATRON_BLOCK_WORDS = re.compile(
        "|".join(_patron_para_palabra(p) for p in _palabras)
    )
else:
    PATRON_BLOCK_WORDS = None


def contiene_palabra_bloqueada(extinf):
    if PATRON_BLOCK_WORDS is None:
        return None
    texto = _quitar_urls_de_atributos(extinf).casefold()
    m = PATRON_BLOCK_WORDS.search(texto)
    if m:
        return m.group(0)
    return None


def obtener_grupo(extinf):
    """Devuelve el group-title original (o None si no tiene)."""
    m = re.search(r'group-title="([^"]*)"', extinf, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def aplicar_prefijo_si_prioritario(extinf, grupo):
    """Añade el prefijo '00 ⭐' solo a los grupos prioritarios."""
    if grupo.casefold() in GRUPOS_PRIORITARIOS:
        nuevo = PREFIJO_GRUPO_PRIORITARIO + grupo
        extinf = re.sub(
            r'group-title="[^"]*"',
            lambda m: f'group-title="{nuevo}"',
            extinf,
            count=1,
            flags=re.IGNORECASE,
        )
        return extinf, True
    return extinf, False


def motivo_descarte(extinf, grupo):
    """Devuelve un texto con el motivo si el canal debe descartarse,
    o None si se acepta."""
    if grupo is None or grupo.casefold() not in CATEGORIAS:
        return f"grupo no permitido: {grupo}"
    if APLICAR_BLOCK_WORDS:
        palabra = contiene_palabra_bloqueada(extinf)
        if palabra:
            return f"palabra bloqueada: {palabra}"
    return None


# ---------------------------------------------------------------------------
# PROCESO PRINCIPAL
# ---------------------------------------------------------------------------

cabecera = f'#EXTM3U url-tvg="{EPG_URL}"'

salida_prioritaria = []
salida = []

try:
    print(f"Descargando: {URL}")
    respuesta = requests.get(URL, timeout=30)
    respuesta.raise_for_status()
    contenido = respuesta.text
    print(f"Bytes descargados: {len(contenido)}")

    lineas = contenido.splitlines()
    if lineas and lineas[0].lstrip("\ufeff").startswith("#EXTM3U"):
        lineas
