import requests
import hashlib
import re
from collections import Counter


URLS = [
    "https://pastebin.com/raw/hV2z2e9g",
    "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_spain.m3u8",
    "https://www.apsattv.com/rakuten_es.m3u",
    "https://raw.githubusercontent.com/minhtienth15/mynote/main/t04.m3u",
]


URL_ES_ONLY = [
    "https://raw.githubusercontent.com/tokoblotongan/88/main/z2.m3u",
]


# Esta lista conservará todos sus canales.
# No se le aplicarán las palabras bloqueadas, pero sí las categorías.
URL_SIN_FILTRO = [
    "https://pastebin.com/raw/hV2z2e9g",
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
    "worldcup club",
    "canal+",
    "france",
    "usa",
    "uk",
    "cbs",
    "afrique",
    "poland",
    "brasil",
    "brazil",
    "cosmote",
    "canada",
    "chicago",
    "cz",
    "sk",
    "cyprus",
    "bar de",
    "denmark",
    "bulgaria",
    "dubai",
    "italy",
    "nl",
    "argentina",
    "espnews",
    "mx",
    "fox sports",
    "fox",
    "fanduel",
    "network",
    "serbia",
    "hgtv",
    "russia",
    "redzone",
    "ngc",
    "nbcny",
    "prima",
    "netherland",
    "austria",
    "sky sport",
    "sony",
    "starz",
    "nz",
    "croatia",
    "sportsnet",
    "supersport",
    "germany",
    "spectrum",
    "ssc sport",
    "hindi",
    "star",
    "tsn",
    "pk",
    "chile",
    "travel",
    "turkey",
    "tennis",
    "sport live",
    "viaplay",
    "sports",
    "wdr",
    "yes",
    "ziggo",
    "zdf",
    "18+",
    "sportv",
    "digi",
    "5sport4k",
    "asia",
    "tv us",
    "channel",
    "🇧🇷",
    "fancode",
    "fast+",
    "rookie",
    "stingray",
    "that's",
    "reuters",
    "collective",
    "vevo pop",
    "vivir con",
    "billiards",
    "league",
    "nba tv",
    "boxing",
    "sportdigital",
    "24/7",
    "mma",
    "soccer",
    "echl",
    "alkass one",
    "israe",
    "sweden",
    "c more",
    "romania",
    "dstv",
    "america",
    "greece",
    "globo",
    "philadelphia",
    "sport",
    "oxygen",
    "football",
    "hockey",
    "tv4",
    "vice",
    "willow",
    "vodafone",
    "3sat",
    "univision",
    "trt",
    "tvp",
    "tv1",
    "tv2",
    "kabel",
    "smartbank",
    "fussball",
    "bein",
    "match!",
]


# Convertimos una sola vez todas las palabras a formato comparable.
BLOCK_WORDS_NORMALIZADAS = {
    palabra.strip().casefold()
    for palabra in BLOCK_WORDS
    if palabra.strip()
}


contador = Counter()


GRUPOS_PROTEGIDOS = [
    "movistar deportes playready",
]


def obtener_categoria(extinf):

    texto = extinf.casefold()

    # DAZN
    if "dazn" in texto:
        return "03 🔥 DAZN"

    # MOVISTAR
    if (
        "movistar" in texto
        or "m+" in texto
    ):
        return "04 ⭐ Movistar+"

    # FÚTBOL
    if any(
        palabra in texto
        for palabra in [
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
            "fútbol",
        ]
    ):
        return "02 ⚽ Fútbol"

    # MOTOR
    if any(
        palabra in texto
        for palabra in [
            "formula 1",
            "fórmula 1",
            "f1",
            "motogp",
            "moto gp",
        ]
    ):
        return "05 🏎️ Motor"

    # DEPORTES
    if any(
        palabra in texto
        for palabra in [
            "eurosport",
            "golf",
            "tennis",
            "tenis",
            "nba",
            "nfl",
            "sport",
            "deporte",
            "vamos",
        ]
    ):
        return "06 🎾 Deportes"

    # CINE
    if any(
        palabra in texto
        for palabra in [
            "cine",
            "movie",
            "movies",
            "cinema",
            "tcm",
        ]
    ):
        return "07 🎬 Cine"

    # SERIES
    if any(
        palabra in texto
        for palabra in [
            "series",
            "axn",
            "fox",
            "warner",
            "syfy",
            "amc",
        ]
    ):
        return "08 📺 Series"

    # DOCUMENTALES
    if any(
        palabra in texto
        for palabra in [
            "discovery",
            "history",
            "historia",
            "nat geo",
            "national geographic",
            "odisea",
        ]
    ):
        return "09 📚 Documentales"

    # INFANTIL
    if any(
        palabra in texto
        for palabra in [
            "disney",
            "nick",
            "nickelodeon",
            "boing",
            "cartoon",
            "clan",
        ]
    ):
        return "10 🧒 Infantil"

    # NOTICIAS
    if any(
        palabra in texto
        for palabra in [
            "cnn",
            "24h",
            "24 horas",
            "euronews",
            "bbc news",
            "news",
        ]
    ):
        return "11 📰 Noticias"

    # MÚSICA
    if any(
        palabra in texto
        for palabra in [
            "mtv",
            "music",
            "música",
            "musica",
            "sol musica",
            "sol música",
            "hit tv",
            "mezzo",
        ]
    ):
        return "12 🎵 Música"

    # GENERALISTAS
    if any(
        palabra in texto
        for palabra in [
            "la 1",
            "la1",
            "la 2",
            "la2",
            "antena 3",
            "telecinco",
            "cuatro",
            "la sexta",
            "lasexta",
            "trece",
            "canal sur",
            "telemadrid",
        ]
    ):
        return "01 📺 Generalistas"

    return "99 📦 Otros"


def limpiar_y_categorizar(extinf):

    grupo_original = re.search(
        r'group-title="([^"]*)"',
        extinf,
        re.IGNORECASE,
    )

    if grupo_original:

        nombre_grupo = grupo_original.group(1).strip()

        if nombre_grupo.casefold() in {
            grupo.casefold()
            for grupo in GRUPOS_PROTEGIDOS
        }:
            contador[nombre_grupo] += 1
            return extinf

    # Eliminar la categoría original
    extinf = re.sub(
        r'\s*group-title="[^"]*"',
        "",
        extinf,
        flags=re.IGNORECASE,
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


def contiene_palabra_bloqueada(texto):

    texto_normalizado = texto.casefold()

    for palabra in BLOCK_WORDS_NORMALIZADAS:

        if palabra in texto_normalizado:
            return palabra

    return None


salida = [
    f'#EXTM3U url-tvg="{EPG_URL}"'
]


for url in URLS + URL_ES_ONLY:

    try:

        print()
        print(f"Descargando: {url}")

        respuesta = requests.get(
            url,
            timeout=30,
        )

        respuesta.raise_for_status()

        contenido = respuesta.text

        print(
            f"Bytes descargados: {len(contenido)}"
        )

        lineas = contenido.splitlines()

        if (
            lineas
            and lineas[0].lstrip("\ufeff").startswith("#EXTM3U")
        ):
            lineas = lineas[1:]

        omitir = False

        for linea in lineas:

            linea = linea.strip()

            if not linea:
                continue

            # Lista que solo conserva entradas marcadas como España
            if url in URL_ES_ONLY:

                if linea.startswith("#EXTINF"):

                    omitir = "┃ES┃".casefold() not in linea.casefold()

                    if not omitir:
                        linea = limpiar_y_categorizar(linea)
                    else:
                        print(
                            f"BLOQUEADO POR NO SER ES -> {linea}"
                        )

                if not omitir:
                    salida.append(linea)

                continue

            # Inicio de un canal nuevo
            if linea.startswith("#EXTINF"):

                # La lista protegida conserva todos sus canales
                if url in URL_SIN_FILTRO:

                    omitir = False
                    linea = limpiar_y_categorizar(linea)

                else:

                    palabra_detectada = contiene_palabra_bloqueada(
                        linea
                    )

                    omitir = palabra_detectada is not None

                    if omitir:

                        print(
                            "BLOQUEADO "
                            f"[{palabra_detectada}] -> {linea}"
                        )

                    else:

                        linea = limpiar_y_categorizar(linea)

            if not omitir:
                salida.append(linea)

    except requests.RequestException as error:

        print(
            f"Error descargando {url}: {error}"
        )

    except Exception as error:

        print(
            f"Error procesando {url}: {error}"
        )


contenido_final = "\n".join(salida) + "\n"


md5 = hashlib.md5(
    contenido_final.encode("utf-8")
).hexdigest()


with open(
    "lista.m3u",
    "w",
    encoding="utf-8",
) as archivo:

    archivo.write(contenido_final)


print()
print("=" * 60)
print("RESUMEN DE CATEGORÍAS")
print("=" * 60)

for categoria, total in sorted(contador.items()):
    print(f"{categoria}: {total}")

print("=" * 60)
print(f"Canales procesados: {sum(contador.values())}")
print(f"MD5: {md5}")
print("lista.m3u creada correctamente")
print("=" * 60)
