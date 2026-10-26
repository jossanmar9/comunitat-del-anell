"""Proves amb dos navegadors: pip install playwright; playwright install chromium.

Executa python build.py i python tests/prova_navegador.py.
PLAYWRIGHT_CHANNEL=msedge permet aprofitar Edge instal·lat.
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
import unittest

from playwright.sync_api import sync_playwright, expect
from prova_servidor import Servidor, partida, free_port


class Navegador(unittest.TestCase):
    def test_sala_pc_i_mobil(self):
        server = Servidor()
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(channel=os.environ.get("PLAYWRIGHT_CHANNEL") or None)
                pc = browser.new_page(locale="ca-ES", viewport={"width": 1280, "height": 900})
                errors = []
                pc.on("pageerror", lambda error: errors.append(str(error)))
                pc.goto(f"http://127.0.0.1:{server.port}/")
                pc.locator("#profile").click()
                expect(pc.locator(".modal h2")).to_have_text("Sala de partida")
                pc.locator("#room-name").fill("Anna Sala")
                pc.locator("#room-race").select_option("elf")
                with pc.expect_response("**/api/players") as response:
                    pc.locator("#room-create button").click()
                created = response.value.json()
                expect(pc.locator(".modal")).to_contain_text("Anota el PIN ara")
                pc.locator("#pin-done").click()
                expect(pc.locator(".modal")).to_contain_text("••••")
                pc.locator(".modal").screenshot(path="/tmp/comunitat-sala-pc.png")
                pc.keyboard.press("Escape")
                pc.locator('[data-lang="es"]').click()
                pc.locator("#profile").click()
                pc.locator(".modal").screenshot(path="/tmp/comunitat-sala-pc-es.png")
                # Host loopback alternatiu: el servidor no l'autoritza com a màster.
                mobile = browser.new_page(locale="es-ES", viewport={"width": 390, "height": 844})
                mobile.on("pageerror", lambda error: errors.append(str(error)))
                mobile.goto(f"http://127.0.0.2:{server.port}/")
                expect(mobile.locator("#join h2")).to_have_text("¿Quién eres?")
                mobile.locator("#j-player").select_option(created["uid"])
                mobile.locator("#j-pin").fill(created["pin"])
                mobile.screenshot(path="/tmp/comunitat-sala-mobil.png")
                mobile.locator('[data-lang="val"]').click()
                expect(mobile.locator("#join h2")).to_have_text("Qui eres?")
                mobile.locator("#j-player").select_option(created["uid"])
                mobile.locator("#j-pin").fill(created["pin"])
                mobile.screenshot(path="/tmp/comunitat-sala-mobil-val.png")
                mobile.locator('[data-lang="es"]').click()
                mobile.locator("#j-player").select_option(created["uid"])
                mobile.locator("#j-pin").fill(created["pin"])
                mobile.locator("#join button[type=submit]").click()
                expect(mobile.locator("#main")).to_contain_text("Espera a que el máster prepare la partida.")
                mobile.reload()
                expect(mobile.locator("#main")).to_contain_text("Espera a que el máster prepare la partida.")
                expect(mobile.locator("#join")).to_have_count(0)
                master = server.master()
                server.post("/api/players", {"action": "revoke", "uid": created["uid"]}, master)
                expect(mobile.locator("#join")).to_be_visible(timeout=15000)
                self.assertFalse(errors, errors)
                browser.close()
        finally:
            server.stop()

    def test_inici_buit_i_alta_amb_la_partida(self):
        server = Servidor(wanted=None)
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(channel=os.environ.get("PLAYWRIGHT_CHANNEL") or None)
                page = browser.new_page(locale="ca-ES")
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.port}/")
                expect(page.locator("#main")).to_contain_text("Cap partida oberta")
                page.screenshot(path="/tmp/comunitat-inici-ca.png", full_page=True)
                page.locator('[data-lang="es"]').click()
                page.screenshot(path="/tmp/comunitat-inici-es.png", full_page=True)
                page.locator('[data-lang="val"]').click()
                page.locator("#welcome-create").click()
                page.locator("#sf-name").fill("Partida nova")
                page.locator("#sf-np").select_option("1")
                page.locator("#sp-name-0").fill("Núria")
                expect(page.locator('#sp-gender-0 option[value="auto"]')).to_have_text("Automàtic: Femení")
                page.locator("#sp-race-0").select_option("elf")
                page.locator("#sf-scen").select_option(index=1)
                page.screenshot(path="/tmp/comunitat-preparacio-ca.png", full_page=True)
                page.locator('[data-lang="es"]').click()
                page.locator("#sf-name").fill("Partida nueva")
                page.locator("#sp-name-0").fill("Núria")
                page.locator("#sp-race-0").select_option("elf")
                page.locator("#sf-scen").select_option(index=1)
                expect(page.locator('#sp-gender-0 option[value="auto"]')).to_have_text("Automático: Femenino")
                page.screenshot(path="/tmp/comunitat-preparacio-es.png", full_page=True)
                page.locator('[data-lang="val"]').click()
                page.locator("#sf-name").fill("Partida nova")
                page.locator("#sp-name-0").fill("Núria")
                page.locator("#sp-race-0").select_option("elf")
                page.locator("#sf-scen").select_option(index=1)
                page.locator("#setup-form button[type=submit]").click()
                expect(page.locator(".modal")).to_contain_text("PIN dels participants")
                expect(page.locator(".modal")).to_contain_text("Núria")
                page.locator("#pins-done").click()
                expect(page.locator(".modal")).to_contain_text("Núria")
                expect(page.locator(".modal")).to_contain_text("••••")
                expect(page.locator(".modal")).to_contain_text("Femení")
                page.keyboard.press("Escape")
                page.reload()
                expect(page.locator("#camp-name")).to_have_value("Partida nova")
                self.assertFalse(errors, errors)
                browser.close()
        finally:
            server.stop()

    def test_galeria_web_fletxes_teclat_i_mobil(self):
        root = Path(__file__).resolve().parent.parent
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run([sys.executable, str(root / "eines/web.py"), directory], check=True, stdout=subprocess.DEVNULL)
            port = free_port()
            server = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", directory], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                for _ in range(50):
                    try:
                        with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=1):
                            break
                    except OSError:
                        time.sleep(.1)
                with sync_playwright() as pw:
                    browser = pw.chromium.launch(channel=os.environ.get("PLAYWRIGHT_CHANNEL") or None)
                    page = browser.new_page(viewport={"width": 1280, "height": 900})
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    for path in ("/", "/es/"):
                        page.goto(f"http://127.0.0.1:{port}{path}")
                        expect(page.locator(".release-news")).to_have_count(0)
                        changelog = page.locator('a[href$="/CHANGELOG.md"]')
                        expect(changelog).to_have_count(1)
                        expect(changelog).to_have_attribute("target", "_blank")
                        expect(changelog).to_have_attribute("rel", "noopener noreferrer")
                        self.assertTrue(page.locator('a[href]:not([href^="#"])').evaluate_all("links => links.every(a => a.target === '_blank' && a.rel.includes('noopener'))"))
                        buttons = page.locator(".miniatures button")
                        count = buttons.count()
                        self.assertGreater(count, 10)
                        first = page.locator("#captura").get_attribute("src")
                        page.locator("#gallery-next").click()
                        expect(page.locator("#gallery-count")).to_have_text(f"2 / {count}")
                        self.assertNotEqual(page.locator("#captura").get_attribute("src"), first)
                        page.locator("#gallery-prev").click()
                        expect(page.locator("#captura")).to_have_attribute("src", first)
                        page.locator("#captures").press("ArrowLeft")
                        expect(page.locator("#gallery-count")).to_have_text(f"{count} / {count}")
                        page.locator("#captures").press("Home")
                        expect(page.locator("#gallery-count")).to_have_text(f"1 / {count}")
                        # Cada nova captura ha d'existir i carregar, en els dos idiomes.
                        for index in range(count):
                            buttons.nth(index).click()
                            page.wait_for_function("document.querySelector('#captura').complete && document.querySelector('#captura').naturalWidth > 0")
                        page.locator("#captures").press("Home")
                        page.locator("#captures").screenshot(path="/tmp/comunitat-galeria-" + ("es" if path == "/es/" else "ca") + ".png")
                    page.set_viewport_size({"width": 390, "height": 844})
                    page.locator("#captura").evaluate("""image => {
                      const start=new Touch({identifier:1,target:image,clientX:300,clientY:100});
                      const end=new Touch({identifier:1,target:image,clientX:100,clientY:110});
                      image.dispatchEvent(new TouchEvent('touchstart',{touches:[start],bubbles:true}));
                      image.dispatchEvent(new TouchEvent('touchend',{changedTouches:[end],bubbles:true}));
                    }""")
                    expect(page.locator("#gallery-count")).to_have_text(f"2 / {count}")
                    page.locator("#captures").screenshot(path="/tmp/comunitat-galeria-mobil.png")
                    self.assertFalse(errors, errors)
                    browser.close()
            finally:
                server.terminate()
                server.wait(10)

    def test_jugada_conflicte_reintent_i_teclat(self):
        server = Servidor()
        try:
            token_a, token_b = server.join("Anna"), server.join("Bernat")
            self.assertEqual(server.write(server.master(), "game/state", partida()), 200)
            with sync_playwright() as pw:
                browser = pw.chromium.launch(channel=os.environ.get("PLAYWRIGHT_CHANNEL") or None)
                contexts, pages, errors = [], [], []
                for token in (token_a, token_b):
                    ctx = browser.new_context(locale="ca-ES", viewport={"width": 1280, "height": 900})
                    ctx.add_init_script("localStorage.setItem('cm-token', %s);localStorage.setItem('cm-lang','val')" % json.dumps(token))
                    page = ctx.new_page()
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto("http://127.0.0.1:%d/" % server.port)
                    expect(page.locator('[data-hope="-1"]')).to_be_visible()
                    contexts.append(ctx)
                    pages.append(page)
                a, b = pages
                hope_a, hope_b = a.locator(".trk .val").first, b.locator(".trk .val").first
                a.locator('[data-hope="-1"]').click()
                expect(a.locator("#save-message")).to_have_text("Guardat")
                expect(hope_b).to_have_text("5/8")
                a.locator("#undo").click()
                expect(hope_a).to_have_text("6/8")
                expect(hope_b).to_have_text("6/8")

                # Reté la petició de Bernat mentre Anna confirma una altra jugada.
                held = []
                b.route("**/api/transaction", lambda route: held.append(route))
                b.locator('[data-hope="-1"]').click()
                b.wait_for_function("document.querySelector('#main').inert")
                self.assertEqual(len(held), 1)
                a.locator('[data-hope="-1"]').click()
                expect(a.locator("#save-message")).to_have_text("Guardat")
                held[0].continue_()
                expect(b.locator("#save-message")).to_contain_text("Un altre jugador")
                expect(hope_b).to_have_text("5/8")
                expect(b.locator("#who")).to_contain_text("Bernat")
                b.unroute("**/api/transaction")

                # Una petició interrompuda queda pendent fins que es reintenta.
                b.route("**/api/transaction", lambda route: route.abort())
                b.locator('[data-hope="-1"]').click()
                expect(b.locator("#save-retry")).to_be_visible()
                _, snap, _ = server.get("/api/snapshot", token_b)
                self.assertEqual(snap["docs"]["game/state"]["hope"], 5)
                b.unroute("**/api/transaction")
                b.locator("#save-retry").click()
                expect(b.locator("#save-message")).to_have_text("Guardat")
                expect(hope_a).to_have_text("4/8")
                expect(hope_b).to_have_text("4/8")

                # Diàleg accessible amb teclat i retorn del focus.
                a.locator("#invite").click()
                expect(a.locator("#qr-close")).to_be_visible()
                a.locator("#qr-close").focus()
                a.keyboard.press("Tab")
                self.assertTrue(a.evaluate("document.querySelector('.modal').contains(document.activeElement)"))
                a.keyboard.press("Shift+Tab")
                expect(a.locator("#qr-close")).to_be_focused()
                a.keyboard.press("Escape")
                expect(a.locator("#invite")).to_be_focused()

                # La resposta es perd després de guardar: el reintent no duplica la jugada.
                def lose_response(route):
                    route.fetch()
                    route.abort()
                b.route("**/api/transaction", lose_response)
                b.locator('[data-hope="-1"]').click()
                expect(b.locator("#save-retry")).to_be_visible()
                _, saved, _ = server.get("/api/snapshot", token_b)
                self.assertEqual(saved["docs"]["game/state"]["hope"], 3)
                b.unroute("**/api/transaction")
                b.locator("#save-retry").click()
                expect(b.locator("#save-message")).to_have_text("Guardat")
                _, retried, _ = server.get("/api/snapshot", token_b)
                self.assertEqual(saved["revision"], retried["revision"])
                expect(hope_a).to_have_text("3/8")

                a.locator("#t-ring").click()
                expect(hope_b).to_have_text("2/8")
                expect(a.locator("#main")).not_to_have_attribute("inert", "")
                # Sense enemics, la cerca de l'Anell es resol també sense diàleg.
                a.wait_for_function("document.querySelector('#side2').textContent.includes('no hi havia natzguls')")

                # Mòbil: els avisos i les pistes no se superposen.
                b.set_viewport_size({"width": 390, "height": 844})
                status = b.locator("#save-status").bounding_box()
                tracks = b.locator("#tracks").bounding_box()
                self.assertGreaterEqual(status["y"], tracks["y"] + tracks["height"] - 1)
                self.assertEqual(errors, [])
                browser.close()
        finally:
            server.stop()


if __name__ == "__main__":
    unittest.main(verbosity=2)
