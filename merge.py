import requests
import hashlib
from collections import defaultdict

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


def classify_channel(name: str) -> str:

    text = name.lower()

    football_words = [
        "laliga",
        "la liga",
        "champions",
        "liga de campeones",
        "premier",
        "bundesliga",
        "serie a",
        "ligue 1",
        "movistar futbol",
        "movistar fútbol",
        "realmadrid",
        "real madrid",
        "barça",
        "barca",
        "dazn laliga",
        "futbol",
        "fútbol"
    ]

    motor_words = [
        "formula 1",
        "f1",
        "motogp",
        "rally",
        "nascar",
        "indycar",
        "racer",
        "top gear"
    ]

    combat_words = [
        "ufc",
        "mma",
        "pfl",
        "boxing",
        "combat",
        "fight"
    ]

    if any(x in text for x in football_words):
        return "Fútbol"

    if any(x in text for x in motor_words):
        return "Motor"

    if any(x in text for x in combat_words):
        return "Combate"

    return "Otros"


channels = []
seen_urls = set()

for source in URLS:

    try:

        print(f"Descargando {source}")

        response = requests.get(
            source,
            timeout=30
        )

        content = response.text

        lines = content.splitlines()

        if lines and lines[0].startswith("#EXTM3U"):
            lines = lines[1:]

        i = 0

        while i < len(lines):

            line = lines[i].strip()

            if not line.startswith("#EXTINF"):
                i += 1
                continue

            if i + 1 >= len(lines):
                break

            extinf = line
            stream_url = lines[i + 1].strip()

            text = extinf.lower()

            if any(word in text for word in BLOCK_WORDS):
                i += 2
                continue

            if stream_url in seen_urls:
                i += 2
                continue

            seen_urls.add(stream_url)

            name = extinf.split(",")[-1].strip()

            channels.append({
                "name": name,
                "category": classify_channel(name),
                "extinf": extinf,
                "url": stream_url
            })

            i += 2

    except Exception as e:

        print(f"Error descargando {source}: {e}")

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

contenido = "\n".join(output)

with open(
    "lista.m3u",
    "w",
    encoding="utf-8"
) as f:

    f.write(contenido)

md5 = hashlib.md5(
    contenido.encode("utf-8")
).hexdigest()

print(f"Canales: {len(channels)}")
print(f"MD5: {md5}")
print("lista.m3u generada correctamente")
