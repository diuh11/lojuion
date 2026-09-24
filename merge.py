import requests
import hashlib
import re
from collections import Counter

URLS = [
    "https://pastebin.com/raw/hV2z2e9g",
    "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_spain.m3u8",
    "https://www.apsattv.com/rakuten_es.m3u"
]

EPG_URL = "http://143.47.50.252:5000/getEPG"

BLOCK_WORDS = [
    "portugal",
    "polsat",
    "israel",
    "méxico",
    "mexico",
    "izzigo",
    "now tv",
    "viasport",
    "cmore",
    "suecia",
    "noruega",
    "allente",
    "vodafone ru",
    "arena sport",
    "bein sports",
    "sports world",
    "worldcup club"
]

contador = Counter()
GRUPOS_PROTEGIDOS = [
"movistar deportes playready"
]
``


def obtener_categoria(extinf):

    texto = extinf.lower()

    # DAZN
    if "dazn" in texto:
        return "03 🔥 DAZN"

    # MOVISTAR
    if (
        "movistar" in texto
        or "m+" in texto
    ):
        return "04 ⭐ Movistar+"

    # FUTBOL
    if any(x in texto for x in [
        "laliga",
        "la liga",
        "champions",
        "liga de campeones",
        "premier league",
        "bundesliga",
        "serie a",
        "ligue 1",
        "uefa",
        "realmadrid",
        "real madrid",
        "hypermotion",
        "copa del rey",
        "futbol",
        "fútbol"
    ]):
        return "02 ⚽ Fútbol"

    # MOTOR
    if any(x in texto for x in [
        "formula 1",
        "f1",
        "motogp",
        "moto gp"
    ]):
        return "05 🏎️ Motor"

    # DEPORTES
    if any(x in texto for x in [
        "eurosport",
        "golf",
        "tennis",
        "nba",
        "nfl",
        "sport",
        "vamos"
    ]):
        return "06 🎾 Deportes"

    # CINE
    if any(x in texto for x in [
        "cine",
        "movie",
        "movies",
        "cinema",
        "tcm"
    ]):
        return "07 🎬 Cine"

    # SERIES
    if any(x in texto for x in [
        "series",
        "axn",
        "fox",
        "warner",
        "syfy",
        "amc"
    ]):
        return "08 📺 Series"

    # DOCUMENTALES
    if any(x in texto for x in [
        "discovery",
        "history",
        "historia",
        "nat geo",
        "national geographic",
        "odisea"
    ]):
        return "09 📚 Documentales"

    # INFANTIL
    if any(x in texto for x in [
        "disney",
        "nick",
        "nickelodeon",
        "boing",
        "cartoon",
        "clan"
    ]):
        return "10 🧒 Infantil"

    # NOTICIAS
    if any(x in texto for x in [
        "cnn",
        "24h",
        "24 horas",
        "euronews",
        "bbc news",
        "news"
    ]):
        return "11 📰 Noticias"

    # MUSICA
    if any(x in texto for x in [
        "mtv",
        "music",
        "sol musica",
        "hit tv",
        "mezzo"
    ]):
        return "12 🎵 Música"

    # GENERALISTAS
    if any(x in texto for x in [
        "la 1",
        "la1",
        "la 2",
        "antena 3",
        "telecinco",
        "cuatro",
        "la sexta",
        "trece",
        "canal sur",
        "telemadrid"
    ]):
        return "01 📺 Generalistas"

    return "99 📦 Otros"


def limpiar_y_categorizar(extinf):

    grupo_original = re.search(
        r'group-title="([^"]*)"',
        extinf,
        re.IGNORECASE
    )

    if grupo_original:

        nombre_grupo = grupo_original.group(1)

        if nombre_grupo.lower() in GRUPOS_PROTEGIDOS:

            contador[nombre_grupo] += 1

            return extinf

    extinf = re.sub(
        r'\s*group-title="[^"]*"',
        '',
        extinf
    )

    categoria = obtener_categoria(extinf)

    contador[categoria] += 1

    if categoria == "99 📦 Otros":
        print(f"SIN CLASIFICAR -> {extinf}")

    pos = extinf.rfind(",")

    if pos != -1:
        extinf = (
            extinf[:pos]
            + f' group-title="{categoria}"'
            + extinf[pos:]
        )

    return extinf


salida = [
    f'#EXTM3U url-tvg="{EPG_URL}"'
]

for url in URLS:

    try:

        print(f"Descargando: {url}")

        contenido = requests.get(
            url,
            timeout=30
        ).text

        print(
            f"Bytes descargados: {len(contenido)}"
        )

        lineas = contenido.splitlines()

        if (
            lineas
            and lineas[0].startswith("#EXTM3U")
        ):
            lineas = lineas[1:]

        omitir = False

        for linea in lineas:

            if linea.startswith("#EXTINF"):

                texto = linea.lower()

                omitir = any(
                    palabra in texto
                    for palabra in BLOCK_WORDS
                )

                if not omitir:
                    linea = limpiar_y_categorizar(linea)

            if not omitir:
                salida.append(linea)

    except Exception as e:

        print(
            f"Error descargando {url}: {e}"
        )

contenido_final = "\n".join(salida)

md5 = hashlib.md5(
    contenido_final.encode("utf-8")
).hexdigest()

with open(
    "lista.m3u",
    "w",
    encoding="utf-8"
) as f:
    f.write(contenido_final)

print()
print("=" * 60)
print("RESUMEN DE CATEGORÍAS")
print("=" * 60)

for categoria, total in sorted(contador.items()):
    print(f"{categoria}: {total}")

print("=" * 60)
print(f"Canales: {(len(salida)-1)//2}")
print(f"MD5: {md5}")
print("lista.m3u creada correctamente")
print("=" * 60)
