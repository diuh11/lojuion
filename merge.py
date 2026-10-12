import requests
import hashlib
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

# ---------------------------------------------------------------------------
# AJUSTES DE COMPROBACIÓN DE CANALES
# ---------------------------------------------------------------------------

COMPROBAR_CANALES = True   # False = no comprobar nada (como antes)
HILOS = 30                 # comprobaciones simultáneas
CONNECT_TIMEOUT = 5        # segundos para conectar
READ_TIMEOUT = 10          # segundos esperando datos
REINTENTOS = 1             # reintentos extra antes de dar un canal por caído

HEADERS_STREAM = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0 Safari/537.36"
}

# ---------------------------------------------------------------------------
# FUENTES
# ---------------------------------------------------------------------------

URLS = [
    "https://pastebin.com/raw/hV2z2e9g",
    "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_spain.m3u8",
    "https://www.apsattv.com/rakuten_es.m3u",
    "https://raw.githubusercontent.com/carmenchica3636/listas-iptv/refs/heads/main/lista_movistar.m3u",
    "https://raw.githubusercontent.com/minhtienth15/mynote/main/t04.m3u",
]

# Esta lista solo conserva canales marcados como España (┃ES┃),
# y SÍ se le aplican las BLOCK_WORDS igual que a las demás.
URL_ES_ONLY = [
    "https://raw.githubusercontent.com/tokoblotongan/88/main/z2.m3u",
]

# Esta lista solo conserva canales cuyo NOMBRE termina en "ES" (como
# palabra suelta, ej. "TVE ES", no "Deportes") o que EMPIEZAN por
# "MOVISTAR". El resto de canales de esta fuente se descarta.
# También pasa por BLOCK_WORDS igual que las demás.
URL_ES_SUFIJO_O_MOVISTAR = [
    "https://raw.githubusercontent.com/tranhoanglanldt-cloud/HLKVN/refs/heads/main/GIAI%20TRI",
]

EPG_URL = "http://143.47.50.252:5000/getEPG"

# ---------------------------------------------------------------------------
# PALABRAS BLOQUEADAS
# ---------------------------------------------------------------------------
# Se aplican a TODAS las fuentes por igual, sin excepciones.
# La coincidencia es por PALABRA COMPLETA (word boundaries), no por
# substring, para evitar falsos positivos como:
#   "star"  dentro de "movistar"   -> NO coincide
#   "sport" dentro de "eurosport"  -> NO coincide
#   "nl"    dentro de "online"     -> NO coincide

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
    "SkySport",
    "CosmoteSportUHD4K",
    "tnt",
    "DSPORTS",
    "Swimming",
    "USHL",
    "QMJHL",
    "OHL",
    "AHL",
    "NLL",
    "Gymnastics",
    "College",
    "WWE",
    "Volleyball",
    "Ice",
    "NHL",
    "QMWHL",
    "NBA | NBA",
    "NCAAW",
    "Basketball",
    "Cricket",
    "DADDYLIVE",
    "https://easyproxy-latest-9tiz.onrender.com",
    "TE24",
    "Squirrel",
    "ZiggoSportUHD",
    "NESN_UHD",
    "sky",
    "skysports",
]

# Convertimos una sola vez todas las palabras a formato comparable y
# compilamos un único patrón con límites de palabra (\b) para evitar
# falsos positivos por coincidencia parcial dentro de otra palabra.


def _patron_para_palabra(palabra):
    """Construye el fragmento de regex para una palabra bloqueada,
    añadiendo \\b solo en los extremos que empiezan/terminan en un
    carácter alfanumérico (para no romper palabras como '18+' o
    'match!', que tienen símbolos en el borde)."""
    prefijo = r"\b" if palabra[0].isalnum() else ""
    sufijo = r"\b" if palabra[-1].isalnum() else ""
    return prefijo + re.escape(palabra) + sufijo


BLOCK_WORDS_NORMALIZADAS = sorted(
    {palabra.strip().casefold() for palabra in BLOCK_WORDS if palabra.strip()},
    key=len,
    reverse=True,
)

PATRON_BLOCK_WORDS = re.compile(
    "|".join(_patron_para_palabra(palabra) for palabra in BLOCK_WORDS_NORMALIZADAS)
)

# Marcas que identifican un canal como "España / Movistar+" dentro de las
# fuentes marcadas como URL_ES_ONLY. Se acepta si contiene [ES], ┃ES┃ o M+
# (por ejemplo "M+ ESTRENOS 1 HD" o "M+ LIGA DE CAMPEONES 1 HD").
PATRON_ES_ONLY = re.compile(
    r"\[es\]|┃es┃|" + re.escape("m+"),
    re.IGNORECASE,
)

# Patrón para la regla: nombre de canal que TERMINA en "ES" como
# palabra suelta (con un límite de palabra antes, para no colar cosas
# como "Deportes", que también termina en "es" pero pegado a la palabra).
PATRON_TERMINA_EN_ES = re.compile(r"\bES\s*$", re.IGNORECASE)

contador = Counter()

GRUPOS_PROTEGIDOS = [
    "movistar deportes playready",
]


# ---------------------------------------------------------------------------
# CATEGORIZACIÓN
# ---------------------------------------------------------------------------

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


def _quitar_urls_de_atributos(extinf):
    """Elimina el contenido de tvg-logo y catchup-source antes de aplicar
    cualquier filtro de palabras. Estas URLs a veces reutilizan logos e
    imágenes de otros países/canales (ej. una carpeta "USA/Fox Network/"
    para un logo genérico de "M+ Estrenos"), y si se dejan en el texto
    provocan bloqueos falsos por palabras como "usa", "fox" o "network"
    que en realidad no describen el canal, sino la ruta de una imagen."""
    texto = re.sub(r'tvg-logo="[^"]*"', '', extinf, flags=re.IGNORECASE)
    texto = re.sub(r'catchup-source="[^"]*"', '', texto, flags=re.IGNORECASE)
    return texto


def contiene_palabra_bloqueada(extinf):
    """Comprueba la línea EXTINF (nombre + atributos: group-title,
    tvg-id, tvg-name...) buscando alguna BLOCK_WORD como PALABRA COMPLETA.
    Esto evita falsos positivos como 'star' dentro de 'movistar' o 'sport'
    dentro de 'eurosport'. Las URLs de tvg-logo/catchup-source se excluyen
    primero para no bloquear canales por culpa de un logo mal etiquetado."""
    texto_normalizado = _quitar_urls_de_atributos(extinf).casefold()
    coincidencia = PATRON_BLOCK_WORDS.search(texto_normalizado)
    return coincidencia.group(0) if coincidencia else None


def _nombre_canal(extinf):
    """Devuelve el nombre visible del canal: el texto que va después de
    la última coma de la línea #EXTINF."""
    pos = extinf.rfind(",")
    if pos == -1:
        return extinf.strip()
    return extinf[pos + 1:].strip()


def cumple_es_o_movistar(extinf):
    """Para las fuentes de URL_ES_SUFIJO_O_MOVISTAR: se acepta el canal
    si su nombre termina en "ES" como palabra suelta (ej. "TVE ES", no
    "Deportes") o si el nombre empieza por "MOVISTAR"."""
    nombre = _nombre_canal(extinf)
    if PATRON_TERMINA_EN_ES.search(nombre):
        return True
    if nombre.strip().casefold().startswith("movistar"):
        return True
    return False


# ---------------------------------------------------------------------------
# COMPROBACIÓN DE CANALES (¿FUNCIONA EL STREAM?)
# ---------------------------------------------------------------------------

def _comprobar_una_vez(url):
    """Un único intento. Devuelve True si el stream parece vivo."""
    with requests.get(
        url,
        headers=HEADERS_STREAM,
        stream=True,
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
        allow_redirects=True,
    ) as r:
        if r.status_code >= 400:
            return False

        ctype = r.headers.get("Content-Type", "").casefold()
        # Una página web (error, login, etc.) no es un stream de vídeo.
        if "text/html" in ctype:
            return False

        es_hls = ".m3u8" in url.casefold() or "mpegurl" in ctype

        if es_hls:
            cuerpo = next(r.iter_content(65536), b"")
            texto = cuerpo.decode("utf-8", "ignore")
            if "#EXTM3U" not in texto:
                return False

            # Buscamos el primer segmento / sub-lista y comprobamos
            # que también responde (muchos canales caídos tienen la
            # lista viva pero los segmentos devuelven 404/403).
            primera = None
            for l in texto.splitlines():
                l = l.strip()
                if l and not l.startswith("#"):
                    primera = urljoin(r.url, l)
                    break
            if primera is None:
                return False

            with requests.get(
                primera,
                headers=HEADERS_STREAM,
                stream=True,
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                allow_redirects=True,
            ) as r2:
                if r2.status_code >= 400:
                    return False
                return bool(next(r2.iter_content(1024), b""))

        # Streams directos (.ts, mp4, etc.): basta con recibir datos.
        return bool(next(r.iter_content(2048), b""))


def canal_funciona(url):
    # Protocolos que requests no sabe probar (rtmp, udp, rtsp...):
    # no podemos comprobarlos, así que los damos por buenos.
    if not url.lower().startswith(("http://", "https://")):
        return True

    for _ in range(REINTENTOS + 1):
        try:
            if _comprobar_una_vez(url):
                return True
        except Exception:
            pass
    return False


def comprobar_urls(urls):
    """Comprueba en paralelo un conjunto de URLs y devuelve
    {url: True/False}."""
    urls = list(urls)
    print()
    print(f"Comprobando {len(urls)} streams ({HILOS} a la vez)...")
    with ThreadPoolExecutor(max_workers=HILOS) as pool:
        resultados = list(pool.map(canal_funciona, urls))
    return dict(zip(urls, resultados))


# ---------------------------------------------------------------------------
# PROCESO PRINCIPAL
# ---------------------------------------------------------------------------

# Cada entrada: {"lines": [#EXTINF, (#EXTVLCOPT...), url], "url": url}
entradas = []

for url in URLS + URL_ES_ONLY + URL_ES_SUFIJO_O_MOVISTAR:
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

        entrada_actual = None

        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue

            # Las etiquetas #EXTGRP (usadas por algunas fuentes, p.ej.
            # GIAI TRI) sustituyen al group-title en muchos reproductores
            # y generaban categorías fantasma (como "SPORTS") que no
            # pasaban por BLOCK_WORDS ni por la categorización. Se
            # descartan siempre, para todas las fuentes.
            if linea.startswith("#EXTGRP"):
                continue

            if linea.startswith("#EXTINF"):
                entrada_actual = None
                texto = _quitar_urls_de_atributos(linea).casefold()

                # Si la fuente es "solo España", primero comprobamos la
                # marca ┃ES┃; si no la lleva, se descarta directamente.
                if url in URL_ES_ONLY:
                    if not PATRON_ES_ONLY.search(texto):
                        print(
                            f"BLOQUEADO POR NO SER [ES]/┃ES┃/M+ -> {linea}"
                        )
                        continue

                # Si la fuente solo admite canales acabados en "ES" o que
                # empiecen por "MOVISTAR" (p.ej. GIAI TRI), el resto se
                # descarta directamente.
                if url in URL_ES_SUFIJO_O_MOVISTAR:
                    if not cumple_es_o_movistar(linea):
                        print(
                            "BLOQUEADO POR NO ACABAR EN 'ES' NI EMPEZAR "
                            f"POR 'MOVISTAR' -> {linea}"
                        )
                        continue

                # A partir de aquí, TODAS las fuentes pasan por el mismo
                # filtro de BLOCK_WORDS, sin excepciones.
                palabra_detectada = contiene_palabra_bloqueada(linea)
                if palabra_detectada is not None:
                    print(
                        "BLOQUEADO "
                        f"[{palabra_detectada}] -> {linea}"
                    )
                    continue

                # Canal aceptado: abrimos una entrada nueva. Todavía NO
                # se categoriza; eso se hace solo si el canal funciona.
                entrada_actual = {"lines": [linea], "url": None}
                entradas.append(entrada_actual)
                continue

            # Líneas que siguen a un #EXTINF (opciones, URL del stream...)
            if entrada_actual is None:
                continue

            entrada_actual["lines"].append(linea)
            if not linea.startswith("#") and entrada_actual["url"] is None:
                entrada_actual["url"] = linea

    except requests.RequestException as error:
        print(
            f"Error descargando {url}: {error}"
        )
    except Exception as error:
        print(
            f"Error procesando {url}: {error}"
        )

# Entradas sin URL de stream: no sirven para nada
entradas = [e for e in entradas if e["url"]]

# ---------------------------------------------------------------------------
# FILTRO DE CANALES CAÍDOS
# ---------------------------------------------------------------------------

if COMPROBAR_CANALES:
    estado = comprobar_urls({e["url"] for e in entradas})
    vivos = 0
    for e in entradas:
        e["caido"] = not estado.get(e["url"])
        if e["caido"]:
            print(f"CAÍDO -> {e['lines'][0]}")
        else:
            vivos += 1
    print(f"Canales vivos: {vivos} / {len(entradas)}")

# ---------------------------------------------------------------------------
# SALIDA: categorizamos solo los canales que funcionan
# ---------------------------------------------------------------------------

salida = [
    f'#EXTM3U url-tvg="{EPG_URL}"'
]

CATEGORIA_CAIDOS = "98 ❌ No funcionan"


def marcar_como_caido(extinf):
    """Sustituye el group-title (sea el que sea, incluidos los grupos
    protegidos) por la categoría de canales que no funcionan."""
    extinf = re.sub(
        r'\s*group-title="[^"]*"',
        "",
        extinf,
        flags=re.IGNORECASE,
    )
    contador[CATEGORIA_CAIDOS] += 1
    pos = extinf.rfind(",")
    if pos != -1:
        extinf = (
            extinf[:pos]
            + f' group-title="{CATEGORIA_CAIDOS}"'
            + extinf[pos:]
        )
    return extinf


for e in entradas:
    if e.get("caido"):
        e["lines"][0] = marcar_como_caido(e["lines"][0])
    else:
        e["lines"][0] = limpiar_y_categorizar(e["lines"][0])
    salida.extend(e["lines"])

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
