import requests
import hashlib

URLS = [
    "https://pastebin.com/raw/hV2z2e9g",
    "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_spain.m3u8",
    "https://www.apsattv.com/rakuten_es.m3u"
]

EPG_URL = "http://143.47.50.252:5000/getEPG"

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

        salida.extend(lineas)

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
print("MERGE SIN FILTROS")
print(f"Lineas: {len(salida)}")
print(f"MD5: {md5}")
print("=" * 50)
``
