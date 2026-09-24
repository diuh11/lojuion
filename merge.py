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

FOOTBALL_WORDS = [
    "laliga",
    "la liga",
    "champions",
    "liga de campeones",
    "premier league",
    "bundesliga",
    "serie a",
    "ligue 1",
    "uefa",
    "football",
    "soccer",
    "movistar futbol",
    "movistar fútbol",
    "m+ futbol",
    "m+ fútbol",
    "dazn laliga",
    "dazn liga",
    "realmadrid",
    "real madrid",
    "barça",
    "barca",
    "hypermotion",
    "laliga tv",
    "laliga inside",
    "copa del rey"
]

REMOVE_GROUPS = [
    "4K UHD",
    "4K",
    "UHD"
]


def is_football_channel(extinf):
    text = extinf.lower()

    return any(
        word in text
        for word in FOOTBALL_WORDS
    )


def get_group(extinf):
    match = re.search(
        r'group-title="([^"]*)"',
        extinf
    )

    if match:
        return match.group(1)

    return None


def set_group(extinf, group_name):
    if 'group-title="' in extinf:

        return re.sub(
            r'group-title="[^"]*"',
            f'group-title="{group_name}"',
            extinf
        )

    pos = extinf.rfind(",")

    if pos == -1:
        return extinf

    return (
        extinf[:pos]
        + f' group-title="{group_name}"'
        + extinf[pos:]
    )


def ensure_group(extinf):
    if 'group-title="' in extinf:
        return extinf

    pos = extinf.rfind(",")

    if pos == -1:
        return extinf

    return (
        extinf[:pos]
        + ' group-title="Sin categorizar"'
        + extinf[pos:]
    )


def normalize_group(extinf):
    current = get_group(extinf)

    if current is None:
        return extinf

    for group in REMOVE_GROUPS:

        if current.lower() == group.lower():

            return set_group(
                extinf,
                "Otros"
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

        i = 0

        while i < len(lineas):

            linea = lineas[i].strip()

            if not linea.startswith("#EXTINF"):
                i += 1
                continue

            if i + 1 >= len(lineas):
                break

            extinf = linea
            stream = lineas[i + 1].strip()

            texto = extinf.lower()

            bloqueado = any(
                palabra in texto
                for palabra in BLOCK_WORDS
            )

            if bloqueado:
                i += 2
                continue

            extinf = normalize_group(extinf)

            extinf = ensure_group(extinf)

            if is_football_channel(extinf):

                grupo_original = get_group(extinf)

                if grupo_original:

                    extinf = set_group(
                        extinf,
                        f"Fútbol | {grupo_original}"
                    )

                else:

                    extinf = set_group(
                        extinf,
                        "Fútbol"
                    )

            salida.append(extinf)
            salida.append(stream)

            i += 2

    except Exception as e:

        print(
            f"Error descargando {url}: {e}"
        )

contenido = "\n".join(salida)

md5 = hashlib.md5(
    contenido.encode("utf-8")
).hexdigest()

with open(
    "lista.m3u",
    "w",
    encoding="utf-8"
) as f:

    f.write(contenido)

print()
print("=" * 50)
print(f"Canales: {(len(salida)-1)//2}")
print(f"MD5: {md5}")
print("lista.m3u generada correctamente")
print("=" * 50)
