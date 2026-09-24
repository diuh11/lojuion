import hashlib
import requests

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


def classify_channel(extinf: str) -> str:

    text = extinf.lower()

    football_keywords = [
        "laliga",
        "la liga",
        "champions",
        "liga de campeones",
        "premier league",
        "bundesliga",
        "serie a",
        "ligue 1",
        "movistar fútbol",
        "movistar futbol",
        "m+ fútbol",
        "m+ futbol",
        "realmadrid",
        "real madrid",
        "barça",
        "barca",
        "soccer",
        "football"
    ]

    motor_keywords = [
        "formula 1",
        "f1",
        "motogp",
        "nascar",
        "rally",
        "racer",
        "top gear"
    ]

    combat_keywords = [
        "mma",
        "ufc",
        "pfl",
        "boxing",
        "fight"
    ]

    if any(word in text for word in football_keywords):
        return "Fútbol"

    if any(word in text for word in motor_keywords):
        return "Motor"

    if any(word in text for word in combat_keywords):
        return "Combate"

    return None


def add_group(extinf: str, category: str) -> str:

    if category is None:
        return extinf

    if 'group-title="' in extinf:

        import re

        return re.sub(
            r'group-title="[^"]*"',
            f'group-title="{category}"',
            extinf
        )

    pos = extinf.rfind(",")

    if pos == -1:
        return extinf

    return (
        extinf[:pos]
        + f' group-title="{category}"'
        + extinf[pos:]
    )


output = [
    f'#EXTM3U url-tvg="{EPG_URL}"'
]

seen_urls = set()

for source in URLS:

    try:

        print(f"Descargando {source}")

        content = requests.get(
            source,
            timeout=30
        ).text

        lines = content.splitlines()

        if (
            lines
            and lines[0].startswith("#EXTM3U")
        ):
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
            url = lines[i + 1].strip()

            lower = extinf.lower()

            blocked = any(
                word in lower
                for word in BLOCK_WORDS
            )

            if blocked:
                i += 2
                continue

            if url in seen_urls:
                i += 2
                continue

            seen_urls.add(url)

            category = classify_channel(
                extinf
            )

            extinf = add_group(
                extinf,
                category
            )

            output.append(extinf)
            output.append(url)

            i += 2

    except Exception as e:

        print(
            f"Error descargando {source}: {e}"
        )

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
print("=" * 50)
print(f"Canales: {(len(output)-1)//2}")
print(f"MD5: {md5}")
print("lista.m3u generada correctamente")
print("=" * 50)
``
