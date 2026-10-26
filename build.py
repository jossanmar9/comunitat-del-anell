#!/usr/bin/env python3
"""Construeix comunitat.py: ajunta la pàgina web de src/web/ (amb les tipografies de src/web/fonts/),
els mapes d'exemple de src/mapes/,
el codi QR de src/qr.py i la finestra de src/finestra.py, i ho incrusta dins del servidor
src/servidor.py, perquè tot el programa siga un sol fitxer.

Ús:  python3 build.py
"""
import base64
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "src" / "web"
MAPES = ROOT / "src" / "mapes"


def read(name):
    return (WEB / name).read_text(encoding="utf-8")


def data_uri(name):
    return "data:image/png;base64," + base64.b64encode((WEB / name).read_bytes()).decode()


def portraits():
    """Els retrats de src/web/personatges/*.webp com a const PORTRAITS = {id: data-uri}."""
    out = {}
    for f in sorted((WEB / "personatges").glob("*.webp")):
        out[f.stem] = "data:image/webp;base64," + base64.b64encode(f.read_bytes()).decode()
    return "const PORTRAITS=" + json.dumps(out) + ";"


# Les tipografies van dins de la pàgina: així l'app es veu igual sense Internet i els mòbils no
# demanen res a cap servidor de fora. Són lliures (SIL Open Font License, src/web/fonts/OFL-*.txt).
FONTS = [  # (família, fitxer, pes, estil)
    ("Alegreya", "alegreya.woff", "400 900", "normal"),
    ("Alegreya", "alegreya-italic.woff", "400 900", "italic"),
    ("Alegreya SC", "alegreya-sc-medium.woff", "500", "normal"),
    ("IM Fell English", "im-fell-english.woff", "400", "normal"),
    ("IM Fell English", "im-fell-english-italic.woff", "400", "italic"),
    ("IM Fell English SC", "im-fell-english-sc.woff", "400", "normal"),
]


def fonts_css(url=None):
    """Les regles @font-face. Per defecte, amb les tipografies incrustades (data:); amb `url`, enllaçades."""
    out = []
    for fam, fitxer, pes, estil in FONTS:
        src = url(fitxer) if url else "data:font/woff;base64," + base64.b64encode((WEB / "fonts" / fitxer).read_bytes()).decode()
        out.append(f'@font-face{{font-family:"{fam}";src:url("{src}") format("woff");font-weight:{pes};'
                   f'font-style:{estil};font-display:swap}}')
    return "\n".join(out)


def b64_lines(data):
    blob = base64.b64encode(data).decode()
    return "\n".join(blob[i:i + 100] for i in range(0, len(blob), 100))


def pagina():
    """La pàgina web completa, en un sol HTML (també la fa servir eines/web.py per a la prova en línia)."""
    page = (
        "<title>La Comunitat</title>\n"
        + "<style>\n" + fonts_css() + "\n" + read("estil-base.css") + "\n" + read("estil.css") + "</style>\n"
        + read("cos.html").replace("__LOGO__", data_uri("logo.png"))
        + "<script>\n" + portraits() + "\n" + read("i18n.js") + "\n" + read("dades.js") + "\n" + read("app.js") + "\n</script>\n"
    )
    return (
        '<!doctype html>\n<html lang="ca">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        f'<link rel="icon" type="image/png" href="{data_uri("favicon.png")}">\n'
        f'<link rel="apple-touch-icon" href="{data_uri("logo.png")}">\n'
        "</head>\n<body>\n" + page + "\n</body>\n</html>\n"
    )


def main():
    server = (ROOT / "src" / "servidor.py").read_text(encoding="utf-8")
    for mark in ("__PAGE__", "__QR__", "__FINESTRA__", "__ICONA__", "__MAPA_VAL__", "__MAPA_ES__"):
        if mark not in server:
            raise SystemExit(f"src/servidor.py no té el marcador {mark}")
    qr = (ROOT / "src" / "qr.py").read_text(encoding="utf-8").strip()
    finestra = (ROOT / "src" / "finestra.py").read_text(encoding="utf-8").strip()
    out = ROOT / "comunitat.py"
    out.write_text(server.replace("__QR__", qr).replace("__FINESTRA__", finestra)
                   .replace("__ICONA__", b64_lines((WEB / "logo.png").read_bytes()))
                   .replace("__MAPA_VAL__", b64_lines((MAPES / "mapa-exemple-val.jpg").read_bytes()))
                   .replace("__MAPA_ES__", b64_lines((MAPES / "mapa-exemple-es.jpg").read_bytes()))
                   .replace("__PAGE__", b64_lines(gzip.compress(pagina().encode("utf-8"), 9))),
                   encoding="utf-8")
    out.chmod(0o755)
    print(f"Fet: {out.name} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
