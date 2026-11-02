#!/usr/bin/env python3
"""Fa les captures dels manuals (docs/imatges/ca i docs/imatges/es) amb una partida d'exemple.

Cal Playwright amb Chromium (pip install playwright). Les dades d'exemple van a una carpeta temporal.

Ús:  python3 build.py && python3 eines/captures.py
"""
import shutil
import os
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
GRAN = {"width": 1360, "height": 860}
MOBIL = {"width": 390, "height": 844}
TEXTOS = {
    "val": {"comencar": "Començar la partida", "partida": "Divendres amb la colla"},
    "es": {"comencar": "Empezar la partida", "partida": "Viernes con la cuadrilla"},
}


def port_lliure():
    with socket.socket() as so:
        so.bind(("127.0.0.1", 0))
        return so.getsockname()[1]


def servidor(dades, port):
    p = subprocess.Popen([sys.executable, str(ROOT / "comunitat.py"), "--sense-finestra", "--sense-navegador",
                          "--port", str(port), "--dades", str(dades)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    return p


def pagina(navegador, lang, mida, url):
    ctx = navegador.new_context(viewport=mida, device_scale_factor=2, locale="es-ES" if lang == "es" else "ca-ES")
    ctx.add_init_script(f"try{{localStorage.setItem('cm-lang','{lang}');localStorage.setItem('cm-theme','light')}}catch(e){{}}")
    pg = ctx.new_page()
    pg.goto(url)
    pg.wait_for_selector("#main .panel, .play")
    pg.wait_for_timeout(500)
    return pg


def clic(pg, sel, n=1):
    for _ in range(n):
        pg.click(sel)
        pg.wait_for_timeout(120)


def captures(lang, carpeta, navegador):
    carpeta.mkdir(parents=True, exist_ok=True)
    T = TEXTOS[lang]
    # Dades fictícies sempre en una carpeta temporal.
    base = Path(tempfile.mkdtemp(prefix="comunitat-captures-"))
    dades = base / ".local" / "share" / "comunitat-del-anell"
    dades.mkdir(parents=True)
    port = port_lliure()
    srv = servidor(dades, port)
    try:
        foto = lambda loc, nom: loc.screenshot(path=str(carpeta / f"{nom}.png"))  # noqa: E731
        url = f"http://127.0.0.1:{port}/"
        pg = pagina(navegador, lang, GRAN, url)
        foto(pg, "00-inici")
        pg.click("#welcome-create")
        pg.fill("#sf-name", T["partida"])

        # Preparació: dos participants i l'escenari de la primera partida
        pg.select_option("#sf-np", "2")
        pg.wait_for_timeout(300)
        pg.fill("#sp-name-0", "Jugador1")
        pg.fill("#sp-name-1", "Jugador2")
        pg.select_option("#sf-scen", index=1)
        pg.wait_for_timeout(300)
        foto(pg.locator("#setup-form"), "03-preparacio")
        pg.click(f"text={T['comencar']}")
        pg.wait_for_timeout(800)
        caselles = pg.locator("#main input[type=checkbox]")
        for i in range(min(4, caselles.count())):
            caselles.nth(i).check()
            pg.wait_for_timeout(120)
        pg.mouse.move(0, 0)
        pg.screenshot(path=str(carpeta / "04-comunitat.png"))

        # Pantalla de joc: dues accions fetes i les eines preparades
        pg.click(".tab[data-tab=partida]")
        pg.wait_for_timeout(500)
        clic(pg, "[data-ap='0:0']")
        clic(pg, "[data-ap='0:1']")
        clic(pg, "[data-cinc=naz]")
        clic(pg, "[data-cinc=troops]", 2)
        clic(pg, "[data-cinc=bFr]")
        clic(pg, "[data-cinc=bSh]", 2)
        pg.locator("[data-cchk=bNaz]").check()
        pg.wait_for_timeout(300)
        pg.mouse.move(0, 0)
        pg.evaluate("scrollTo(0, 0)")
        pg.screenshot(path=str(carpeta / "05-partida.png"))

        clic(pg, "[data-ap='0:2']")
        clic(pg, "[data-ap='0:3']")
        clic(pg, "[data-ap='1:0']")
        clic(pg, "#acts-done")
        clic(pg, "#draw2")
        pg.wait_for_timeout(300)
        foto(pg.locator("#side2 ol.steps"), "07-torn")

        pg.click("#shadow-card")
        pg.wait_for_selector(".modal")
        foto(pg.locator(".modal"), "08-ombra")
        pg.click("#sc-cancel")

        pg.click("#skies")
        pg.wait_for_selector(".modal")
        radios = pg.locator(".modal input[type=radio]")
        if radios.count() > 1:
            radios.nth(1).check()
        pg.wait_for_timeout(200)
        foto(pg.locator(".modal"), "09-cel")
        pg.click("#sk-cancel")

        eines = pg.locator(".tools > section.tool")
        foto(eines.nth(0), "10-cerca")
        pg.click("#t-search")
        pg.wait_for_selector("#fc")
        clic(pg, ".modal [data-inc=slip]")
        clic(pg, ".modal [data-inc=tired]")
        clic(pg, ".modal [data-inc=call]")
        foto(pg.locator(".modal"), "11-cerca-daus")
        pg.click("#fok")
        pg.wait_for_timeout(500)
        pg.keyboard.press("Escape")

        foto(eines.nth(1), "12-batalla")
        pg.click("#t-battle")
        pg.wait_for_selector("#fc")
        clic(pg, ".modal [data-inc=rout]")
        clic(pg, ".modal [data-inc=naz]")
        foto(pg.locator(".modal"), "13-batalla-daus")
        pg.click("#fok")
        pg.wait_for_selector(".modal")
        pg.wait_for_timeout(300)
        foto(pg.locator(".modal"), "14-batalla-result")
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(300)
        foto(eines.nth(3), "15-anell")
        foto(eines.nth(2), "16-esperanca")
        pg.set_viewport_size({"width": GRAN["width"], "height": 1000})
        pg.evaluate("scrollTo(0, 0)")
        pg.wait_for_timeout(300)
        side = pg.locator("#side2").bounding_box()
        pg.screenshot(path=str(carpeta / "17-registre.png"),
                      clip={"x": side["x"], "y": side["y"], "width": side["width"], "height": min(760, 1000 - side["y"])})
        pg.set_viewport_size(GRAN)

        # Al mòbil, un altre jugador
        mob = pagina(navegador, lang, MOBIL, url)
        mob.click(".tab[data-tab=partida]")
        mob.wait_for_timeout(600)
        mob.screenshot(path=str(carpeta / "21-mobil.png"))
        mob.context.close()

        # Es perd la partida: el resum
        while pg.locator(".modal").count() == 0:
            pg.click("[data-hope='-1']")
            pg.wait_for_timeout(200)
        pg.wait_for_timeout(400)
        foto(pg.locator(".modal"), "18-resum")
        pg.keyboard.press("Escape")

        # Les còpies de seguretat de la partida
        pg.click(".tab[data-tab=partides]")
        pg.click("[data-cbak]")
        pg.wait_for_selector("#bak-box")
        n = pg.locator("[data-brest]").count()
        pg.click("#bak-now")
        pg.wait_for_function(f"document.querySelectorAll('[data-brest]').length > {n}")
        pg.wait_for_timeout(1800)
        foto(pg.locator(".modal"), "22-copies")
        pg.keyboard.press("Escape")

        # Una partida nova i la pestanya Partides
        pg.click(".tab[data-tab=partides]")
        pg.wait_for_selector("#cn-name")
        pg.fill("#cn-name", T["partida"])
        pg.click("#camp-new button[type=submit]")
        pg.wait_for_timeout(2500)
        pg.click(".tab[data-tab=partides]")
        pg.wait_for_selector(".camp-card")
        pg.wait_for_selector(".hist-card")
        # La carpeta de dades de veritat és temporal: es mostra la de Linux d'un usuari d'exemple
        pg.evaluate("document.querySelector('.here .path').textContent='/home/jugador1/.local/share/comunitat-del-anell'")
        pg.mouse.move(0, 0)
        pg.wait_for_timeout(300)
        main = pg.locator("#main")
        hist = pg.locator("#hist").bounding_box()
        pg.set_viewport_size({"width": GRAN["width"], "height": int(hist["y"] + hist["height"] + 40)})
        pg.wait_for_timeout(300)
        caixa = main.bounding_box()
        here = pg.locator(".here").bounding_box()
        hist = pg.locator("#hist").bounding_box()
        h2 = pg.locator("#main h2").nth(1).bounding_box()
        pg.screenshot(path=str(carpeta / "19-partides.png"), full_page=True,
                      clip={"x": caixa["x"], "y": caixa["y"], "width": 1000, "height": here["y"] + here["height"] + 24 - caixa["y"]})
        pg.screenshot(path=str(carpeta / "20-historial.png"), full_page=True,
                      clip={"x": caixa["x"], "y": h2["y"] - 16, "width": 1000, "height": hist["y"] + hist["height"] + 24 - h2["y"] + 16})
        pg.context.close()
    finally:
        srv.terminate()
        srv.wait(10)
        shutil.rmtree(base, ignore_errors=True)


def jpeg(carpeta):
    """Passa les captures a JPEG, a 1600 px d'amplada com a màxim."""
    from PIL import Image
    for vella in ("00-inici-v270.png", "01-entrada-v260.png", "01-sala-v260.png", "03-preparacio-v270.png",
                  "01-entrada.jpg", "02-qr.jpg"):
        (carpeta / vella).unlink(missing_ok=True)   # de la taula connectada, que ja no hi és
    for png in sorted(carpeta.glob("*.png")):
        im = Image.open(png).convert("RGB")
        if im.width > 1600:
            im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
        im.save(png.with_suffix(".jpg"), quality=84, optimize=True, progressive=True)
        png.unlink()


def main():
    with sync_playwright() as p:
        # En entorns on Playwright no porta Chromium propi, reutilitza el navegador del sistema.
        chromium = os.environ.get("CHROMIUM") or shutil.which("chromium") or shutil.which("chromium-browser")
        navegador = p.chromium.launch(executable_path=chromium) if chromium else p.chromium.launch()
        for lang, nom in (("val", "ca"), ("es", "es")):
            carpeta = ROOT / "docs" / "imatges" / nom
            captures(lang, carpeta, navegador)
            jpeg(carpeta)
            print(f"Fet: docs/imatges/{nom}")
        navegador.close()


if __name__ == "__main__":
    main()
