import requests

URLS = [
    "https://pastebin.com/raw/hV2z2e9g",
    "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_spain.m3u8",
    "https://www.apsattv.com/rakuten_es.m3u"
]

salida = ["#EXTM3U"]

for url in URLS:
    try:
        print(f"Descargando {url}")
        contenido = requests.get(url, timeout=30).text

        lineas = contenido.splitlines()

        if lineas and lineas[0].startswith("#EXTM3U"):
            lineas = lineas[1:]

        salida.extend(lineas)

    except Exception as e:
        print(f"Error: {e}")

with open("lista.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(salida))

print("Lista creada correctamente")
