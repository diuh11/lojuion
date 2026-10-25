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

# Si lo pones en True, además del filtro por categoría se aplicarán las
# BLOCK_WORDS. Por defecto está en False porque ya filtras por categoría y
# esa lista tan grande (sport, sky, tnt, uk, usa...) podría eliminar
# canales que sí quieres.
APLICAR_BLOCK_WORDS = False

BLOCK_WORDS = [
    "portugal", "polsat", "israel", "méxico", "mexico", "france", "usa", "uk",
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
PATRON_BLOCK_WORDS = (
    re.compile("|".join(_patron_para_palabra(p) for p in _palabras))
    if _palabras
    else None
)


def contiene_palabra_bloqueada(extinf):
    if not PATRON_BLOCK_WORDS:
        return None
    texto = _quitar_urls_de_atributos(extinf).casefold()
    m = PATRON_BLOCK_WORDS.search(texto)
    return m.group(0) if m else None


def obtener_grupo(extinf):
    """Devuelve el group-title original (o None si no tiene)."""
    m = re.search(r'group-title="([^"]*)"', extinf, re.IGNORECASE)
    return m.group(1).strip() if m else None


def aplicar_prefijo_si_prioritario(extinf, grupo):
    """Mantiene el nombre de grupo original; solo añade el prefijo '00 ⭐'
    a los grupos prioritarios para que salgan los primeros."""
    if grupo.casefold() in GRUPOS_PRIORITARIOS:
        nuevo = PREFIJO_GRUPO_PRIORITARIO + grupo
        return re.sub(
            r'group-title="[^"]*"',
            lambda m: f'group-title="{nuevo}"',
            extinf,
            count=1,
            flags=re.IGNORECASE,
        ), True
    return extinf, False


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
        lineas = lineas[1:]

    omitir = True          # hasta que un #EXTINF válido lo cambie
    destino = salida

    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue

        # Las etiquetas #EXTGRP se descartan siempre.
        if linea.startswith("#EXTGRP"):
            continue

        if linea.startswith("#EXTINF"):
            grupo = obtener_grupo(linea)

            # 1) Filtro por categoría
            if grupo is None or grupo.casefold() not in CATEGORIAS:
                omitir = True
                print(f"DESCARTADO (grupo: {grupo}) -> {linea}")
                continue

            # 2) Filtro opcional por palabras bloqueadas
            if APLICAR_BLOCK_WORDS:
