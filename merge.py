import hashlib
import re
from collections import Counter

import requests

URL = "https://pastebin.com/raw/hV2z2e9g"
EPG_URL = "http://143.47.50.252:5000/getEPG"

CATEGORIAS = {
    "movistar deportes fairplay",
    "dazn hls",
    "movistar deportes playready",
    "dazn",
}

GRUPOS_PRIORITARIOS = {
    "movistar deportes fairplay",
}
PREFIJO_GRUPO_PRIORITARIO = "00 ⭐ "


def obtener_grupo(extinf):
    m = re.search(r'group-title="([^"]*)"', extinf, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    return None


def poner_prefijo(extinf, grupo):
    nuevo = PREFIJO_GRUPO_PRIORITARIO + grupo
    return re.sub(
        r'group-title="[^"]*"',
        lambda m: 'group-title="' + nuevo + '"',
        extinf,
        count=1,
        flags=re.IGNORECASE,
    )


def descargar_lineas(url):
    print("Descargando: " + url)
    respuesta = requests.get(url, timeout=30)
    respuesta.raise_for_status()
    texto = respuesta.text
    print("Bytes descargados: " + str(len(texto)))
    lineas = texto.splitlines()
    if lineas and lineas[0].lstrip("\ufeff").startswith("#EXTM3U"):
        lineas = lineas[1:]
    return lineas


def procesar(lineas):
    contador = Counter()
    prioritarios = []
    normales = []
    destino = normales
    omitir = True

    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue
        if linea.startswith("#EXTGRP"):
            continue

        if linea.startswith("#EXTINF"):
            grupo = obtener_grupo(linea)
            if grupo is None or grupo.casefold() not in CATEGORIAS:
                omitir = True
                continue

            omitir = False
            if grupo.casefold() in GRUPOS_PRIORITARIOS:
                linea = poner_prefijo(linea, grupo)
                destino = prioritarios
            else:
                destino = normales
            contador[obtener_grupo(linea)] += 1

        if not omitir:
            destino.append(linea)

    return prioritarios, normales, contador


def main():
    lineas = descargar_lineas(URL)
    prioritarios, normales, contador = procesar(lineas)

    cabecera = '#EXTM3U url-tvg="' + EPG_URL + '"'
    contenido = "\n".join([cabecera] + prioritarios + normales) + "\n"
    md5 = hashlib.md5(contenido.encode("utf-8")).hexdigest()

    with open("lista.m3u", "w", encoding="utf-8") as f:
        f.write(contenido)

    print()
    print("=" * 60)
    for categoria, total in sorted(contador.items()):
        print(categoria + ": " + str(total))
    print("Canales procesados: " + str(sum(contador.values())))
    print("MD5: " + md5)
    print("lista.m3u creada correctamente")
    print("=" * 60)


main()
