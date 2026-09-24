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
    "worldcup club",
]

salida = [
    f'#EXTM3U url-tvg="{EPG_URL}"'
]

seen_urls = set()

for source in URLS:

    try:

        print(f"Descargando: {source}")

        contenido = requests.get(
            source,
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

        i = 0

        while i < len(lineas):

            linea = lineas[i].strip()

            if not linea.startswith("#EXTINF"):
                i += 1
                continue

            extinf = linea

            if i + 1 >= len(lineas):
                break

            url = lineas[i + 1].strip()

            texto = extinf.lower()

            omitir = any(
                palabra in texto
                for palabra in BLOCK_WORDS
            )

            if omitir:
                i += 2
                continue

            url_key = url.lower()

            if url_key in seen_urls:
                i += 2
                continue

            seen_urls.add(url_key)

            salida.append(extinf)
            salida.append(url)

            i += 2

    except Exception as e:

        print(
            f"Error descargando {source}: {e}"
        )

contenido_final = "\n".join(salida)

hash_md5 = hashlib.md5(
    contenido_final.encode("utf-8")
).hexdigest()

print(
    f"Canales finales: {(len(salida)-1)//2}"
)

print(
    f"Hash MD5: {hash_md5}"
)

with open(
    "lista.m3u",
    "w",
    encoding="utf-8"
) as f:

    f.write(contenido_final)

print(
    "lista.m3u generada correctamente"
)
