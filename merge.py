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


def limpiar_grupo(extinf):

    extinf = re.sub(
        r'\s*group-title="[^"]*"',
        '',
        extinf
    )

    if 'group-title=' not in extinf:

        pos = extinf.rfind(",")

        if pos != -1:

            extinf = (
                extinf[:pos]
                + ' group-title="General"'
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

                    linea = limpiar_grupo(
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
