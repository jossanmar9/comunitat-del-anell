#!/usr/bin/env python3
"""Construeix La Comunitat a partir de src/.

    python3 build.py              fa comunitat.py, el programa per a Windows i Linux: la pàgina de src/web/
                                  (amb les tipografies de src/web/fonts/), els mapes d'exemple de src/mapes/,
                                  la persistència de src/persistencia.py i la finestra de src/finestra.py,
                                  dins del servidor local src/servidor.py; tot en un sol fitxer.
    python3 build.py --web DIR    fa l'app web (per a la web i per a Android) a la carpeta DIR: la mateixa
                                  pàgina, que guarda les partides al navegador, i el que cal per a instal·lar-la.
"""
import base64
import gzip
import json
import re
import shutil
import sys
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


def versio():
    return re.search(r'^VERSION = "([^"]+)"', (ROOT / "src" / "servidor.py").read_text(encoding="utf-8"), re.M).group(1)


SCRIPTS = ["i18n.js", "dades.js", "magatzem.js", "app.js"]


def pagina(entorn="escriptori"):
    """La pàgina de l'app en un sol HTML. `entorn`: "escriptori" (guarda a través del programa) o "web"
    (guarda al navegador: la web i l'app d'Android)."""
    page = (
        "<title>La Comunitat</title>\n"
        + "<style>\n" + fonts_css() + "\n" + read("estil-base.css") + "\n" + read("estil.css") + "</style>\n"
        + read("cos.html").replace("__LOGO__", data_uri("logo.png"))
        + "<script>\n" + f"const ENTORN={json.dumps(entorn)},VERSIO={json.dumps(versio())};\n" + portraits() + "\n"
        + "\n".join(read(s) for s in SCRIPTS) + "\n</script>\n"
    )
    web = ""
    if entorn == "web":
        web = ('<link rel="manifest" href="manifest.webmanifest">\n'
               '<meta name="theme-color" content="#8C2A1C">\n'
               '<meta name="mobile-web-app-capable" content="yes">\n')
    return (
        '<!doctype html>\n<html lang="ca">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
        f'<link rel="icon" type="image/png" href="{data_uri("favicon.png")}">\n'
        f'<link rel="apple-touch-icon" href="{data_uri("logo.png")}">\n' + web +
        "</head>\n<body>\n" + page + "\n</body>\n</html>\n"
    )


def icona(mida, mascara=False):
    """La icona de l'app (per a la pantalla d'inici d'Android), feta a partir de logo.png."""
    from PIL import Image
    logo = Image.open(ROOT / "logo.png").convert("RGBA")
    fons = Image.new("RGBA", (mida, mida), (233, 220, 188, 255))
    interior = int(mida * (0.66 if mascara else 0.9))
    logo.thumbnail((interior, interior), Image.LANCZOS)
    fons.alpha_composite(logo, ((mida - logo.width) // 2, (mida - logo.height) // 2))
    return fons.convert("RGB")


def web(eixida):
    """L'app web instal·lable (PWA): index.html, manifest, service worker, icones i mapes d'exemple."""
    eixida = Path(eixida)
    eixida.mkdir(parents=True, exist_ok=True)
    v = versio()
    (eixida / "index.html").write_text(pagina("web"), encoding="utf-8")
    for lang in ("val", "es"):
        shutil.copy(MAPES / f"mapa-exemple-{lang}.jpg", eixida / f"mapa-exemple-{lang}.jpg")
    icones = [("icona-192.png", 192, False), ("icona-512.png", 512, False), ("icona-mascara-512.png", 512, True)]
    for nom, mida, mascara in icones:
        icona(mida, mascara).save(eixida / nom, optimize=True)
    manifest = {
        "name": "La Comunitat", "short_name": "La Comunitat",
        "description": "Ajudant lliure per a portar les partides d'«El Señor de los Anillos: El Destino de la Comunidad».",
        "lang": "ca", "start_url": "./", "scope": "./", "display": "standalone", "orientation": "any",
        "background_color": "#E9DCBC", "theme_color": "#8C2A1C",
        "icons": [{"src": "icona-192.png", "sizes": "192x192", "type": "image/png"},
                  {"src": "icona-512.png", "sizes": "512x512", "type": "image/png"},
                  {"src": "icona-mascara-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"}],
    }
    (eixida / "manifest.webmanifest").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    fitxers = ["./", "index.html", "manifest.webmanifest", "mapa-exemple-val.jpg", "mapa-exemple-es.jpg"] + [n for n, _, _ in icones]
    (eixida / "sw.js").write_text(SERVICE_WORKER.replace("__VERSIO__", v).replace("__FITXERS__", json.dumps(fitxers)),
                                  encoding="utf-8")
    print(f"Fet: app web a {eixida}")


# Funciona sense Internet: la primera vegada es guarda tot l'app; després, primer es mira la còpia guardada.
# Cada versió nova té una memòria cau nova i esborra les velles.
SERVICE_WORKER = """// La Comunitat __VERSIO__: l'app funciona sense Internet.
const CAU='la-comunitat-__VERSIO__',FITXERS=__FITXERS__;
self.addEventListener('install',e=>{e.waitUntil(caches.open(CAU).then(c=>c.addAll(FITXERS)).then(()=>self.skipWaiting()))});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CAU).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET'||new URL(e.request.url).origin!==location.origin)return;
  e.respondWith(caches.match(e.request,{ignoreSearch:true}).then(r=>r||fetch(e.request)));
});
"""


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--web":
        return web(sys.argv[2])
    if len(sys.argv) != 1:
        raise SystemExit(__doc__)
    server = (ROOT / "src" / "servidor.py").read_text(encoding="utf-8")
    for mark in ("__PAGE__", "__FINESTRA__", "__PERSISTENCIA__", "__ICONA__", "__MAPA_VAL__", "__MAPA_ES__"):
        if mark not in server:
            raise SystemExit(f"src/servidor.py no té el marcador {mark}")
    finestra = (ROOT / "src" / "finestra.py").read_text(encoding="utf-8").strip()
    out = ROOT / "comunitat.py"
    out.write_text(server.replace("__FINESTRA__", finestra)
                   .replace("__PERSISTENCIA__", (ROOT / "src" / "persistencia.py").read_text(encoding="utf-8").strip())
                   .replace("__ICONA__", b64_lines((WEB / "logo.png").read_bytes()))
                   .replace("__MAPA_VAL__", b64_lines((MAPES / "mapa-exemple-val.jpg").read_bytes()))
                   .replace("__MAPA_ES__", b64_lines((MAPES / "mapa-exemple-es.jpg").read_bytes()))
                   .replace("__PAGE__", b64_lines(gzip.compress(pagina().encode("utf-8"), 9, mtime=0))),
                   encoding="utf-8")
    out.chmod(0o755)
    print(f"Fet: {out.name} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
