#!/usr/bin/env python3
"""Prova de punta a punta de l'app en un navegador de veritat (cal Playwright amb Chromium).

Es prova dues vegades: la versió d'escriptori (comunitat.py, que guarda a la carpeta de dades) i la
versió web/Android (build.py --web, que guarda al navegador). En totes dues: crear una partida,
jugar, recarregar i que s'haja guardat, perdre-la i que vaja a l'historial, còpies, exportar,
importar, duplicar i esborrar.

Ús:  python3 build.py && python3 tests/prova_app.py
"""
import http.server
import json
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from functools import partial
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent


def port_lliure():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Base:
    """Les mateixes proves per a les dues versions; cada subclasse diu com s'arranca."""

    def obri(self):
        self.pg = self.ctx.new_page()
        self.errors = []
        self.pg.on("pageerror", lambda e: self.errors.append(str(e)))
        self.pg.goto(self.url)
        self.pg.wait_for_selector("#main .panel, #setup-form, .play", timeout=15000)

    def tearDown(self):
        self.assertEqual(self.errors, [], "errors de JavaScript a la pàgina")

    def prepara(self, nom="Divendres"):
        pg = self.pg
        pg.click("#welcome-create")
        pg.fill("#sf-name", nom)
        pg.select_option("#sf-np", "2")
        pg.fill("#sp-name-0", "Jugador1")
        pg.fill("#sp-name-1", "Jugador2")
        pg.select_option("#sf-scen", index=1)
        pg.click("#setup-form button[type=submit]")
        pg.wait_for_selector(".tab[data-tab=comunitat][aria-selected=true]")

    def test_partida_completa(self):
        self.obri()
        pg = self.pg
        self.assertTrue(pg.is_visible("#welcome-create"))
        self.prepara()
        self.assertEqual(pg.input_value("#camp-name"), "Divendres")
        pg.click(".tab[data-tab=partida]")
        pg.click("[data-ap='0:0']")
        pg.click("[data-hope='-1']")
        pg.wait_for_timeout(600)
        self.assertIn("5", pg.inner_text("#tracks .trk .val"))
        # Es recarrega: tot continua igual
        pg.reload()
        pg.wait_for_selector(".play")
        self.assertIn("5", pg.inner_text("#tracks .trk .val"))
        self.assertEqual(pg.input_value("#camp-name"), "Divendres")
        # Es perd la partida: resum i historial
        for _ in range(5):
            pg.click("[data-hope='-1']")
            pg.wait_for_timeout(150)
        pg.wait_for_selector(".modal")
        self.assertIn("Derrota", pg.inner_text(".modal"))
        pg.keyboard.press("Escape")
        pg.click(".tab[data-tab=partides]")
        pg.wait_for_selector(".hist-card")
        self.assertIn("Divendres", pg.inner_text("#hist"))
        # Desfer la derrota la lleva de l'historial
        pg.click(".tab[data-tab=partida]")
        pg.click("#undo")
        pg.wait_for_timeout(500)
        pg.click(".tab[data-tab=partides]")
        pg.wait_for_selector("#hist p.muted")
        # Còpies: n'hi ha almenys una en obrir; se'n fa una a mà i es restaura
        pg.click("[data-cbak]")
        pg.wait_for_selector("#bak-box")
        n = pg.locator("[data-brest]").count()
        pg.click("#bak-now")
        pg.wait_for_function(f"document.querySelectorAll('[data-brest]').length > {n}")
        pg.click("[data-brest] >> nth=0")
        pg.click("[data-brest] >> nth=0")
        pg.wait_for_timeout(800)
        self.assertFalse(pg.is_visible("#bak-box"), pg.inner_text("#toast"))
        # Duplicar i esborrar (va a la paperera i es recupera)
        pg.click(".tab[data-tab=partides]")
        pg.click("[data-cdup]")
        pg.wait_for_selector("text=Divendres (còpia)")
        card = pg.locator(".camp-card", has_text="Divendres (còpia)")
        card.locator("[data-cdel]").click()
        card.locator("[data-cdel]").click()
        pg.wait_for_selector("[data-undelete]")
        pg.click("[data-undelete]")
        pg.wait_for_selector("text=Divendres (còpia)")
        # Importar una partida exportada
        exp = self.exporta()
        self.assertEqual(json.loads(exp)["format"], "comunitat-del-anell")
        pg.set_input_files("#camp-imp", files=[{"name": "p.json", "mimeType": "application/json", "buffer": exp.encode()}])
        pg.wait_for_selector("text=Divendres (importada)")
        # Obrir una altra partida
        pg.locator(".camp-card", has_text="Divendres (importada)").locator("[data-copen]").click()
        pg.wait_for_selector(".tab[data-tab=partida][aria-selected=true]")
        self.assertEqual(pg.input_value("#camp-name"), "Divendres (importada)")
        # En tornar a obrir l'app, s'obri l'última partida
        pg.reload()
        pg.wait_for_timeout(1000)
        self.assertEqual(pg.input_value("#camp-name"), "Divendres (importada)")

    def test_idioma(self):
        self.obri()
        self.pg.click("[data-lang=es]")
        self.assertIn("Partidas", self.pg.inner_text(".tabs"))


class ProvaEscriptori(Base, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = sync_playwright().start()
        cls.nav = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.nav.close()
        cls.pw.stop()

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="comunitat-app-"))
        self.baixades = self.dir / "home"
        (self.baixades / "Downloads").mkdir(parents=True)
        port = port_lliure()
        env = dict(__import__("os").environ, HOME=str(self.baixades))
        self.proc = subprocess.Popen([sys.executable, str(ROOT / "comunitat.py"), "--sense-finestra", "--port", str(port),
                                      "--dades", str(self.dir / "dades")], stdout=subprocess.DEVNULL,
                                     stderr=subprocess.PIPE, env=env)
        self.url = f"http://127.0.0.1:{port}/"
        time.sleep(1.2)
        self.ctx = self.nav.new_context()

    def tearDown(self):
        self.ctx.close()
        self.proc.terminate()
        self.proc.wait(10)
        shutil.rmtree(self.dir, ignore_errors=True)
        super().tearDown()

    def exporta(self):
        self.pg.locator(".camp-card", has_text="Divendres").first.locator("[data-cexp]").click()
        self.pg.wait_for_timeout(800)
        fitxers = list((self.baixades / "Downloads").glob("*.json"))
        self.assertEqual(len(fitxers), 1)
        return fitxers[0].read_text(encoding="utf-8")

    def test_dades_al_disc(self):
        self.obri()
        self.prepara("Dissabte")
        self.pg.wait_for_timeout(500)
        f = self.dir / "dades" / "partides" / "dissabte.json"
        self.assertTrue(f.exists())
        self.assertEqual(json.loads(f.read_text(encoding="utf-8"))["docs"]["campaign/main"]["name"], "Dissabte")
        # Al principi encara no hi ha res a copiar; en obrir-la una altra vegada, sí.
        self.pg.reload()
        self.pg.wait_for_timeout(800)
        self.assertTrue(list((self.dir / "dades" / "copies" / "dissabte").glob("*-obrir.json")))


class ProvaWeb(Base, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = Path(tempfile.mkdtemp(prefix="comunitat-web-"))
        subprocess.run([sys.executable, str(ROOT / "build.py"), "--web", str(cls.dir)], check=True, stdout=subprocess.DEVNULL)
        handler = partial(http.server.SimpleHTTPRequestHandler, directory=str(cls.dir))
        handler.log_message = lambda *a: None
        cls.http = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.http.serve_forever, daemon=True).start()
        cls.pw = sync_playwright().start()
        cls.nav = cls.pw.chromium.launch()

    @classmethod
    def tearDownClass(cls):
        cls.nav.close()
        cls.pw.stop()
        cls.http.shutdown()
        shutil.rmtree(cls.dir, ignore_errors=True)

    def setUp(self):
        self.url = f"http://127.0.0.1:{self.http.server_address[1]}/"
        self.ctx = self.nav.new_context(accept_downloads=True)

    def tearDown(self):
        self.ctx.close()
        super().tearDown()

    def exporta(self):
        with self.pg.expect_download() as d:
            self.pg.locator(".camp-card", has_text="Divendres").first.locator("[data-cexp]").click()
        return Path(d.value.path()).read_text(encoding="utf-8")

    def test_mapa_propi(self):
        self.obri()
        self.prepara()
        self.pg.click(".tab[data-tab=partida]")
        png = (ROOT / "logo.png").read_bytes()
        self.pg.set_input_files("#map-file", files=[{"name": "m.png", "mimeType": "image/png", "buffer": png}])
        self.pg.wait_for_selector("#map-reset")
        self.assertTrue(self.pg.get_attribute("#map-img", "src").startswith("data:image/jpeg"))
        self.pg.reload()
        self.pg.wait_for_selector("#map-reset")


if __name__ == "__main__":
    unittest.main(verbosity=2)
