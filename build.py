#!/usr/bin/env python3
"""Construeix comunitat.py: ajunta la pàgina web de src/web/ i la incrusta dins
del servidor src/servidor.py, perquè tot el programa siga un sol fitxer.

Ús:  python3 build.py
"""
import base64
import gzip
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "src" / "web"


def read(name):
    return (WEB / name).read_text(encoding="utf-8")


def main():
    page = (
        "<title>Comunitat de l'Anell</title>\n"
        + read("fonts.html")
        + "<style>\n" + read("estil-base.css") + "\n" + read("estil.css") + "</style>\n"
        + read("cos.html")
        + "<script>\n" + read("dades.js") + "\n" + read("app.js") + "\n</script>\n"
    )
    html = (
        '<!doctype html>\n<html lang="ca">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        "</head>\n<body>\n" + page + "\n</body>\n</html>\n"
    )
    blob = base64.b64encode(gzip.compress(html.encode("utf-8"), 9)).decode()
    lines = "\n".join(blob[i:i + 100] for i in range(0, len(blob), 100))
    server = (ROOT / "src" / "servidor.py").read_text(encoding="utf-8")
    if "__PAGE__" not in server:
        raise SystemExit("src/servidor.py no té el marcador __PAGE__")
    out = ROOT / "comunitat.py"
    out.write_text(server.replace("__PAGE__", lines), encoding="utf-8")
    out.chmod(0o755)
    print(f"Fet: {out.name} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
