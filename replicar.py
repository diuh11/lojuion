#!/usr/bin/env python3
"""
Replica lista.m3u en DESTINO/ como TOTAL archivos .m3u con nombre
de 5 caracteres aleatorios (ej. a7k2x.m3u).

- Los nombres se crean UNA sola vez y se conservan (las URLs no cambian).
- Si lista.m3u cambia, todos los archivos se actualizan.
- Solo escribe los archivos que realmente cambian.
- NO toca ninguna otra carpeta (listas/, copias/, etc.).
"""
import os
import secrets
import string
import sys
from pathlib import Path

ORIGEN = Path("lista.m3u")
DESTINO = Path("listas2")
TOTAL = 200
ALFABETO = string.ascii_lowercase + string.digits


def nombre_nuevo(usados):
    while True:
        nombre = "".join(secrets.choice(ALFABETO) for _ in range(5))
        if nombre not in usados:
            return nombre


def main():
    if not ORIGEN.is_file():
        sys.exit(f"No existe {ORIGEN}")

    contenido = ORIGEN.read_bytes()

    # Seguridad: si el original está vacío o roto, no machacamos las réplicas.
    if not contenido.lstrip(b"\xef\xbb\xbf").startswith(b"#EXTM3U"):
        sys.exit("lista.m3u no parece una lista válida; no se replica.")

    DESTINO.mkdir(exist_ok=True)

    nombres = {p.stem for p in DESTINO.glob("*.m3u")}
    creadas = 0
    while len(nombres) < TOTAL:
        nombres.add(nombre_nuevo(nombres))
        creadas += 1

    actualizadas = 0
    for nombre in sorted(nombres):
        ruta = DESTINO / f"{nombre}.m3u"
        if not ruta.exists() or ruta.read_bytes() != contenido:
            ruta.write_bytes(contenido)
            actualizadas += 1

    print(f"Réplicas totales: {len(nombres)} | nuevas: {creadas} | escritas: {actualizadas}")

    repo = os.environ.get("GITHUB_REPOSITORY")
    if repo:
        for nombre in sorted(nombres):
            print(f"https://raw.githubusercontent.com/{repo}/main/{DESTINO}/{nombre}.m3u")


if __name__ == "__main__":
    main()
