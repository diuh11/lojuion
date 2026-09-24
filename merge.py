...
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

            extinf = normalize_group(
                extinf
            )

            extinf = ensure_group(
                extinf
            )

            if is_football_channel(extinf):

                grupo_original = get_group(
                    extinf
                )

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
