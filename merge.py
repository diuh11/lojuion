import requests

URLS = [
    "https://pastebin.com/raw/hV2z2e9g",
    "https://raw.githubusercontent.com/Free-TV/IPTV/refs/heads/master/playlists/playlist_spain.m3u8",
    "https://www.apsattv.com/rakuten_es.m3u"
]

salida = [
    '#EXTM3U url-tvg="http://143.47.50.252:5000/getEPG"'
]

omitir = False

for url in URLS:
    try:
        print(f"Descargando {url}")
        contenido = requests.get(url, timeout=30).text

        lineas = contenido.splitlines()

        if lineas and lineas[0].startswith("#EXTM3U"):
            lineas = lineas[1:]

        for linea in lineas:

            if linea.startswith("#EXTINF"):

                texto = linea.lower()

                omitir = (
                    "portugal" in texto or
                    "polsat" in texto or
                    "israel" in texto or
                    "méxico" in texto or
                    "mexico" in texto or
                    "izzigo" in texto or
                    "now tv" in texto or
                    "viasport" in texto or
                    "cmore" in texto or
                    "suecia" in texto or
                    "noruega" in texto or
                    "allente" in texto or
                    "vodafone ru" in texto or
                    "arena sport" in texto or
                    "bein sports" in texto or
                    "sports world" in texto or
                    "worldcup club" in texto
                )

            if not omitir:
                salida.append(linea)

    except Exception as e:
        print(f"Error: {e}")

with open("lista.m3u", "w", encoding="utf-8") as f:
    f.write("\n".join(salida))

print("Lista creada correctamente")
import hashlib

contenido_final = "\n".join(salida)

# Calcular hash MD5 del contenido
hash_md5 = hashlib.md5(contenido_final.encode("utf-8")).hexdigest()

print(f"Total líneas generadas: {len(salida)}")
print(f"Hash MD5: {hash_md5}")

with open("lista.m3u", "w", encoding="utf-8") as f:
    f.write(contenido_final)

print("Lista creada correctamente")
