import re
import hashlib
import requests

# =========================================================
# FUENTES
# =========================================================

URLS = [
    "https://pastebin.com/raw/hV2z2e9g",
    "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_spain.m3u8",
    "https://www.apsattv.com/rakuten_es.m3u"
]

EPG_URL = "http://143.47.50.252:5000/getEPG"

# =========================================================
# ORDEN DE SALIDA
# =========================================================

CATEGORY_ORDER = [
    "Películas",
    "Series",
    "Infantil",
    "Documentales",
    "Crimen y Misterio",
    "Reality",
    "Entretenimiento",
    "Música",
    "Deportes",
    "Motor",
    "Combate",
    "Estilo de vida",
    "Noticias",
    "Otros",
]

# =========================================================
# PRIORIDAD DE DETECCIÓN
# =========================================================

DETECTION_PRIORITY = [
    "Infantil",
    "Combate",
    "Motor",
    "Crimen y Misterio",
    "Reality",
    "Documentales",
    "Películas",
    "Series",
    "Música",
    "Estilo de vida",
    "Noticias",
    "Deportes",
    "Entretenimiento",
]

# =========================================================
# BLOQUEOS
# =========================================================

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
]

# =========================================================
# NORMALIZACIÓN
# =========================================================

RENAME_RULES = {
    "Películas Románticas - Rakuten TV": "Películas Románticas",
    "Pelis Top - Rakuten TV": "Pelis Top",
    "Sci-Fi - Rakuten TV": "Sci‑Fi",
    "Thrillers - Rakuten TV": "Thrillers",
    "Royalworld - Nobleza y dinastías": "Royalworld",
}


def normalize_name(name):
    name = name.strip()

    if name in RENAME_RULES:
        name = RENAME_RULES[name]

    for suffix in [
        " - Rakuten TV",
        " | Rakuten TV",
    ]:
        if name.endswith(suffix):
            name = name[:-len(suffix)]

    return name.strip()


# =========================================================
# CLASIFICACIÓN DIRECTA
# =========================================================

EXACT_CHANNELS = {

    "Pingu": "Infantil",
    "Pocoyó": "Infantil",

    "PFL MMA": "Combate",

    "RACER International": "Motor",
    "Rally.TV FAST+": "Motor",
    "Top Gear en español": "Motor",

    "Todo Crimen": "Crimen y Misterio",
    "Rookie Blue": "Crimen y Misterio",

    "Pilotos del Ártico": "Reality",
    "Shark Tank": "Reality",

    "Planeta Salvaje": "Documentales",
    "Royalworld": "Documentales",
    "Terra Mater WILD": "Documentales",
    "Weather Spy": "Documentales",

    "Películas Románticas": "Películas",
    "Pelis Top": "Películas",
    "Sci‑Fi": "Películas",
    "Thrillers": "Películas",
    "Verdi TV": "Películas",

    "Rakuten VIKI": "Series",
    "Sony One | Éxitos": "Series",
    "Sony One | Series Comedia": "Series",
    "Todo Drama": "Series",
    "Todo Novelas": "Series",
    "wedotv Amor": "Series",
    "Yu-Gi-Oh!": "Series",

    "People Are Awesome": "Entretenimiento",
    "Revry": "Entretenimiento",
    "The Pet Collective": "Entretenimiento",

    "Qello Concerts by Stingray": "Música",
    "Qwest TV": "Música",
    "Vevo Latino": "Música",
    "Vevo Pop": "Música",

    "Stingray Exitos Latinos": "Música",
    "Stingray Greatest Hits": "Música",
    "Stingray Total Hits Spain": "Música",
    "Stingray: Remember the 80’s": "Música",

    "That's 70s": "Música",
    "That's 80s": "Música",
    "That's 90s00s": "Música",
    "That's ROCK": "Música",

    "Stingray Naturescape": "Estilo de vida",
    "Travelxp": "Estilo de vida",
    "The Design Network": "Estilo de vida",
    "Vivir con gatos": "Estilo de vida",
    "Vivir con perros": "Estilo de vida",

    "The Reuters 60": "Noticias",

    "Red Bull TV": "Deportes",
    "Sports Illustrated TV": "Deportes",
    "Surf Channel": "Deportes",
    "World Surf League 24/7": "Deportes",
    "TOP Barça": "Deportes",
    "World Billiards TV": "Deportes",
    "Tennis+": "Deportes",
}

# =========================================================
# KEYWORDS
# =========================================================

CATEGORY_KEYWORDS = {

    "Infantil": [
        "kids", "children", "cartoon", "animation",
        "junior", "baby", "pingu", "pocoyo",
        "maya", "mellizas"
    ],

    "Combate": [
        "mma", "ufc", "pfl", "bellator",
        "fight", "boxing", "kickboxing",
        "combat", "muay thai"
    ],

    "Motor": [
        "motorsport", "motorsports",
        "rally", "racer", "nascar",
        "indycar", "formula 1",
        "f1", "motogp", "wrc",
        "top gear"
    ],

    "Crimen y Misterio": [
        "crime", "criminal", "detective",
        "murder", "forensic", "mystery",
        "police", "investigation"
    ],

    "Reality": [
        "reality",
        "shark tank",
        "ice pilots",
        "pilots"
    ],

    "Documentales": [
        "documentary",
        "nature",
        "wildlife",
        "animals",
        "history",
        "science",
        "biography",
        "weather",
        "monarchy",
        "dynasty"
    ],

    "Películas": [
        "movie",
        "movies",
        "film",
        "cinema",
        "sci-fi",
        "thriller"
    ],

    "Series": [
        "series",
        "soap",
        "novelas",
        "drama",
        "romance",
        "sitcom",
        "viki"
    ],

    "Música": [
        "music",
        "concerts",
        "stingray",
        "vevo",
        "rock",
        "jazz",
        "latino",
        "70s",
        "80s",
        "90s",
        "00s",
        "hits",
        "qwest",
        "qello",
    ],

    "Estilo de vida": [
        "travel",
        "design",
        "home",
        "garden",
        "naturescape",
        "relax",
        "cats",
        "dogs",
        "ambience",
    ],

    "Noticias": [
        "news",
        "reuters",
    ],

    "Deportes": [
        "sports",
        "tennis",
        "surf",
        "league",
        "football",
        "soccer",
        "barça",
        "billiards",
    ],

    "Entretenimiento": [
        "awesome",
        "viral",
        "fails",
        "pets",
        "clips",
        "entertainment",
    ]
}

# =========================================================
# UTILIDADES
# =========================================================

def classify_channel(name, extinf):

    clean_name = normalize_name(name)

    if clean_name in EXACT_CHANNELS:
        return EXACT_CHANNELS[clean_name]

    text = f"{clean_name} {extinf}".lower()

    for category in DETECTION_PRIORITY:

        words = CATEGORY_KEYWORDS.get(category, [])

        for word in words:

            if word.lower() in text:
                return category

    return "Otros"


def extract_name(extinf):
    return extinf.split(",")[-1].strip()


# =========================================================
# DESCARGA
# =========================================================

channels = []
seen_urls = set()
seen_names = set()

for source in URLS:

    try:

        print("Descargando:", source)

        content = requests.get(
            source,
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

            url = lines[i + 1].strip()

            lower = extinf.lower()

            skip = any(
                word in lower
                for word in BLOCK_WORDS
            )

            if skip:
                i += 2
                continue

            name = extract_name(extinf)
            name = normalize_name(name)

            url_key = url.lower()
            name_key = name.lower()

            if url_key in seen_urls:
                i += 2
                continue

            if name_key in seen_names:
                i += 2
                continue

            seen_urls.add(url_key)
            seen_names.add(name_key)

            category = classify_channel(
                name,
                extinf
            )

            extinf = re.sub(
                r'group-title="[^"]*"',
                f'group-title="{category}"',
                extinf
            )

            if 'group-title="' not in extinf:
                extinf = extinf.replace(
                    ",",
                    f' group-title="{category}",',
                    1
                )

            channels.append({
                "category": category,
                "extinf": extinf,
                "url": url
            })

            i += 2

    except Exception as e:
        print("Error:", e)

# =========================================================
# GENERACIÓN M3U
# =========================================================

output = [
    f'#EXTM3U url-tvg="{EPG_URL}"'
]

for category in CATEGORY_ORDER:

    group_channels = [
        x for x in channels
        if x["category"] == category
    ]

    group_channels.sort(
        key=lambda x:
        x["extinf"].lower()
    )

    for channel in group_channels:

        output.append(channel["extinf"])
        output.append(channel["url"])

content = "\n".join(output)

hash_md5 = hashlib.md5(
    content.encode("utf-8")
).hexdigest()

with open(
    "lista.m3u",
    "w",
    encoding="utf-8"
) as f:
    f.write(content)

print("Canales:", len(channels))
print("MD5:", hash_md5)
print("lista.m3u generada")
