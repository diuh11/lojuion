import requests

URLS = [
    "https://pastebin.com/raw/hV2z2e9g",
    "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_spain.m3u8",
    "https://www.apsattv.com/rakuten_es.m3u"
]

salida = ["#EXTM3U"]

for url in URLS:

    try:

        print(f"Descargando: {url}")

        respuesta = requests.get(
            url,
            timeout=30
        )

        respuesta.raise_for_status()

        contenido = respuesta.text

        print(
            f"Bytes descargados: {len(contenido)}"
        )

        if "movistar" in contenido.lower():
            print(
                f"MOVISTAR ENCONTRADO EN {url}"
            )

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

with open(
    "lista.m3u",
    "w",
    encoding="utf-8"
) as f:

    f.write(
        "\n".join(salida)
    )

print()
print("=" * 50)
print(f"Lineas generadas: {len(salida)}")
print("lista.m3u creada correctamente")
print("=" * 50)
