import requests
import hashlib

URLS = [
    "https://pastebin.com/raw/hV2z2e9g",
    "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_spain.m3u8",
    "https://www.apsattv.com/rakuten_es.m3u"
]

salida = [
    '#EXTM3U url-tvg="http://143.47.50.252:5000/getEPG"'
]

vistos = set()

for url in URLS:

    try:

        print(f"Descargando: {url}")

        contenido = requests.get(
            url,
            timeout=30
        ).text

        lineas = contenido.splitlines()

        if lineas and lineas[0].startswith("#EXTM3U"):
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

            if stream in vistos:
                i += 2
                continue

            vistos.add(stream)

            salida.append(extinf)
            salida.append(stream)

            i += 2

    except Exception as e:

        print(f"Error: {e}")

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

print(f"MD5: {md5}")
print("OK")
