import requests
import re

URLS = [
    "https://pastebin.com/raw/hV2z2e9g",
    "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_spain.m3u8",
    "https://www.apsattv.com/rakuten_es.m3u"
]

EXCLUIR = [
    "portugal",
    "mexico",
    "méxico",
    "polsat",
    "vodafone ru",
    "now tv",
    "viasport",
    "suecia",
    "noruega",
    "worldcup club"
]

salida = [
    '#EXTM3U url-tvg="http://143.47.50.252:5000/getEPG"'
]

for url in URLS:
    try:
        print(f"Descargando {url}")

        contenido = requests.get(url, timeout=30).text
        lineas = contenido.splitlines()

        if lineas and lineas[0].startswith("#EXTM3U"):
            lineas = lineas[1:]

        i = 0

        while i < len(lineas):

            if lineas[i].startswith("#EXTINF"):

                extinf = lineas[i]

                enlace = ""
                if i + 1 < len(lineas):
                    enlace = lineas[i + 1]

                grupo = ""

                match = re.search(
                    r'group-title="([^"]*)"',
                    extinf,
                    re.IGNORECASE
                )

                if match:
                    grupo = match.group(1).lower()

                if any(x in grupo for x in EXCLUIR):
                    i += 2
                    continue

                salida.append(extinf)
                salida.append(enlace)

                i += 2

            else:
                i += 1

    except Exception as e:
        print(f"Error: {e}")

with open("lista.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(salida))

print("Lista creada correctamente")
