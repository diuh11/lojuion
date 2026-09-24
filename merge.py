import requests
import hashlib
import re

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


def obtener_categoria(extinf):

    texto = extinf.lower()

    # FÚTBOL
    if any(x in texto for x in [
        "laliga",
        "la liga",
        "champions",
        "liga de campeones",
        "dazn laliga",
        "hypermotion",
        "real madrid",
        "realmadrid",
        "copa del rey",
        "uefa",
        "premier league",
        "bundesliga",
        "serie a",
        "ligue 1",
        "fútbol",
        "futbol"
    ]):
        return "Fútbol"

    # MOTOR
    if any(x in texto for x in [
        "formula 1",
        "f1",
        "motogp",
        "moto gp",
        "motor"
    ]):
        return "Motor"

    # DEPORTES
    if any(x in texto for x in [
        "eurosport",
        "golf",
        "tennis",
        "nba",
        "nfl",
        "deportes",
        "sport tv",
        "vamos"
    ]):
        return "Deportes"

    # CINE
    if any(x in texto for x in [
        "cine",
        "cinema",
        "movie",
        "movies",
        "hollywood",
        "tcm"
    ]):
        return "Cine"

    # SERIES
    if any(x in texto for x in [
        "series",
        "axn",
        "fox",
        "warner",
        "syfy",
        "amc",
        "comedy central"
    ]):
        return "Series"

    # DOCUMENTALES
    if any(x in texto for x in [
        "discovery",
        "historia",
        "history",
        "national geographic",
        "nat geo",
        "odisea",
        "documental"
    ]):
        return "Documentales"

    # INFANTIL
    if any(x in texto for x in [
        "disney",
        "nick",
        "nickelodeon",
        "boing",
        "cartoon",
        "clan",
        "baby tv"
    ]):
        return "Infantil"

    # NOTICIAS
    if any(x in texto for x in [
        "24h",
        "24 horas",
        "cnn",
        "bbc news",
        "euronews",
        "al jazeera",
        "news"
    ]):
        return "Noticias"

    # MÚSICA
    if any(x in texto for x in [
        "mtv",
        "music",
        "mezzo",
        "sol musica",
        "hit tv"
    ]):
        return "Música"

    # GENERALISTAS ESPAÑA
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
        return "TV Generalista"

    return "Otros"


def limpiar_y_categorizar(extinf):

    extinf = re.sub(
        r'\s*group-title="[^"]*"',
        '',
        extinf
    )

    categoria = obtener_categoria(
        extinf
    )

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

                    linea = limpiar_y_categorizar(
                        linea
                    )

            if not omitir:
                salida.append(linea)

    except Exception as e:

        print(
            f"Error descargando {url}: {e}"
        )

contenido_final = "\n".join(salida)

hash_md5 = hashlib.md5(
    contenido_final.encode("utf-8")
).hexdigest()

with open(
    "lista.m3u",
    "w",
    encoding="utf-8"
) as f:

    f.write(contenido_final)

print()
print("=" * 50)
print(f"Total líneas: {len(salida)}")
print(f"MD5: {hash_md5}")
print("Lista creada correctamente")
print("=" * 50)
