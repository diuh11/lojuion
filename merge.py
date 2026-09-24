import requests
import hashlib
import re
from collections import defaultdict

# =====================================================
# FUENTES
# =====================================================

URLS = [
    "https://pastebin.com/raw/hV2z2e9g",
    "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_spain.m3u8",
    "https://www.apsattv.com/rakuten_es.m3u"
]

EPG_URL = "http://143.47.50.252:5000/getEPG"

# =====================================================
# FILTROS
# =====================================================

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

# =====================================================
# PRIORIDAD
# =====================================================

CATEGORY_ORDER = [
    "Fútbol",
    "Motor",
    "Combate",
    "Deportes",
    "Películas",
    "Series",
    "Infantil",
    "Documentales",
    "Crimen y Misterio",
    "Reality",
    "Entretenimiento",
    "Música",
    "Estilo de vida",
    "Noticias",
    "Otros"
]

# =====================================================
# NORMALIZACIÓN
# =====================================================

def normalize_name(name):

    rules = {
        "Películas Románticas - Rakuten TV":
            "Películas Románticas",

        "Pelis Top - Rakuten TV":
            "Pelis Top",

        "Sci-Fi - Rakuten TV":
            "Sci‑Fi",

        "Thrillers - Rakuten TV":
            "Thrillers",

        "Royalworld - Nobleza y dinastías":
            "Royalworld",
    }

    return rules.get(name.strip(), name.strip())


# =====================================================
# FUTBOL
# =====================================================

FOOTBALL_WORDS = [

    "laliga",
    "la liga",

    "champions",
    "liga de campeones",

    "premier league",
    "bundesliga",
    "serie a",
    "ligue 1",

    "football",
    "soccer",

    "movistar futbol",
    "m+ futbol",
    "futbol",

    "realmadrid",
    "real madrid tv",

    "barça",
    "barca",

    "dazn laliga",

    "top barça"
]

# =====================================================
# MOTORES
# =====================================================

MOTOR_WORDS = [
    "f1",
    "formula 1",
    "motogp",
    "nascar",
    "indycar",
    "rally",
    "racer",
    "top gear",
    "motorsport",
    "motorsports"
]

# =====================================================
# COMBATE
# =====================================================

COMBAT_WORDS = [
    "mma",
    "ufc",
    "pfl",
    "boxing",
    "combat",
    "fight",
    "kickboxing"
]

# =====================================================
# CLASIFICACIÓN
# =====================================================

def classify_channel(name, extinf):

    text = f"{name} {extinf}".lower()

    if any(x in text for x in FOOTBALL_WORDS):
        return "Fútbol"

    if any(x in text for x in MOTOR_WORDS):
        return "Motor"

    if any(x in text for x in COMBAT_WORDS):
        return "Combate"

    if "movie" in text or "película" in text:
        return "Películas"

    if "documentary" in text:
        return "Documentales"

    if "music" in text or "stingray" in text or "vevo" in text:
        return "Música"

    if "news" in text or "reuters" in text:
        return "Noticias"

    if "series" in text:
        return "Series"

    return "Otros"


# =====================================================
# PARSEO M3U
# =====================================================

channels = []

seen_urls = set()

for url in URLS:

    try:

        print(f"Descargando {url}")

        content = requests.get(
            url,
            timeout=30
        ).text

        lines = content.splitlines()

        if lines and lines[0].startswith("#EXTM3U"):
            lines = lines[1:]

        i = 0

        while i < len(lines):

            line = lines[i].strip()

            if not line.startswith("#EXTINF"):
                i += 1
                continue

            extinf = line

            if i + 1 >= len(lines):
                break

            stream_url = lines[i + 1].strip()

            text = extinf.lower()

            if any(
                word in text
                for word in BLOCK_WORDS
            ):
                i += 2
                continue

            if stream_url in seen_urls:

                i += 2
                continue

            seen_urls.add(stream_url)

            name = normalize_name(
                extinf.split(",")[-1]
            )

            category = classify_channel(
                name,
                extinf
            )

            channels.append({
                "name": name,
                "category": category,
                "extinf": extinf,
                "url": stream_url
            })

            i += 2

    except Exception as e:

        print(
            f"Error en {url}: {e}"
        )

# =====================================================
# GENERAR SALIDA
# =====================================================

groups = defaultdict(list)

for channel in channels:
    groups[channel["category"]].append(channel)

output = [
    f'#EXTM3U url-tvg="{EPG_URL}"'
]

for category in CATEGORY_ORDER:

    if category not in groups:
        continue

    groups[category].sort(
        key=lambda x: x["name"].lower()
    )

    for channel in groupsoutput.append(channel["extinf"])
        output.append(channel["url"])

# canales no clasificados

for channel in groups["Otros"]:

    output.append(channel["extinf"])
    output.append(channel["url"])

content = "\n".join(output)

with open(
    "lista.m3u",
    "w",
    encoding="utf-8"
) as f:

    f.write(content)

md5 = hashlib.md5(
    content.encode("utf-8")
).hexdigest()

print()
print("===================================")
print(f"Canales: {len(channels)}")
print(f"MD5: {md5}")
print("lista.m3u generada")
print("===================================")
