#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Personalitza el projecte d'Android que genera Capacitor (`npx cap add android`): la versió, les
icones, la pantalla d'inici i els colors. Cal Pillow.

Ús:  python3 eines/android.py --versio 3.0.0 paquets/android/android
"""
import argparse
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
PERGAMI = (233, 220, 188)        # #E9DCBC, el color de fons de l'app
DENSITATS = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}


def codi_versio(versio):
    """3.0.0 → 30000; 3.12.4 → 31204. Android només deixa actualitzar si el número creix."""
    m = re.fullmatch(r"(\d+)\.(\d+)(?:\.(\d+))?", versio)
    if not m:
        raise SystemExit(f"Versió no vàlida: {versio}")
    a, b, c = (int(x or 0) for x in m.groups())
    if b > 99 or c > 99:
        raise SystemExit("La versió menor i el pedaç han de ser menors de 100.")
    return a * 10000 + b * 100 + c


def logo(mida):
    im = Image.open(ROOT / "logo.png").convert("RGBA")
    im.thumbnail((mida, mida), Image.LANCZOS)
    return im


def centrat(fons, im):
    fons.alpha_composite(im, ((fons.width - im.width) // 2, (fons.height - im.height) // 2))
    return fons


def icones(res):
    for nom, f in DENSITATS.items():
        d = res / f"mipmap-{nom}"
        d.mkdir(parents=True, exist_ok=True)
        m = round(48 * f)
        quadrada = centrat(Image.new("RGBA", (m, m), PERGAMI + (255,)), logo(round(m * 0.86)))
        quadrada.convert("RGB").save(d / "ic_launcher.png", optimize=True)
        mascara = Image.new("L", (m * 4, m * 4), 0)
        ImageDraw.Draw(mascara).ellipse((0, 0, m * 4 - 1, m * 4 - 1), fill=255)
        rodona = Image.new("RGBA", (m, m), (0, 0, 0, 0))
        rodona.paste(centrat(Image.new("RGBA", (m, m), PERGAMI + (255,)), logo(round(m * 0.72))), (0, 0),
                     mascara.resize((m, m), Image.LANCZOS))
        rodona.save(d / "ic_launcher_round.png", optimize=True)
        # Icona adaptativa: 108 dp, i el que es veu segur és el cercle central de 66 dp
        a = round(108 * f)
        centrat(Image.new("RGBA", (a, a), (0, 0, 0, 0)), logo(round(a * 0.58))).save(d / "ic_launcher_foreground.png", optimize=True)
    fons = res / "values" / "ic_launcher_background.xml"
    fons.write_text('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
                    '    <color name="ic_launcher_background">#E9DCBC</color>\n</resources>\n', encoding="utf-8")


def inici(res):
    """La imatge que es veu mentre s'obri l'app (Capacitor en posa una de seua)."""
    for f in res.glob("drawable*/splash.png"):
        w, h = Image.open(f).size
        centrat(Image.new("RGBA", (w, h), PERGAMI + (255,)), logo(round(min(w, h) * 0.45))).convert("RGB").save(f, optimize=True)


def versio(app, v):
    gradle = app / "build.gradle"
    text = gradle.read_text(encoding="utf-8")
    nou, n1 = re.subn(r"versionCode \d+", f"versionCode {codi_versio(v)}", text)
    nou, n2 = re.subn(r'versionName "[^"]*"', f'versionName "{v}"', nou)
    if not (n1 and n2):
        raise SystemExit(f"No trobe versionCode/versionName a {gradle}")
    gradle.write_text(nou, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--versio", required=True)
    ap.add_argument("projecte", type=Path, help="la carpeta android/ que ha creat Capacitor")
    a = ap.parse_args()
    app = a.projecte / "app"
    res = app / "src" / "main" / "res"
    if not res.is_dir():
        raise SystemExit(f"No és un projecte de Capacitor: {a.projecte}")
    versio(app, a.versio)
    icones(res)
    inici(res)
    print(f"Fet: Android {a.versio} (codi {codi_versio(a.versio)})")


if __name__ == "__main__":
    sys.exit(main())
