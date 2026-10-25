"""Proves amb dos navegadors: pip install playwright; playwright install chromium.

Executa python build.py i python tests/prova_navegador.py.
PLAYWRIGHT_CHANNEL=msedge permet aprofitar Edge instal·lat.
"""
import json
import os
import unittest

from playwright.sync_api import sync_playwright, expect
from prova_servidor import Servidor, partida


class Navegador(unittest.TestCase):
    def test_jugada_conflicte_reintent_i_teclat(self):
        server = Servidor()
        try:
            token_a, token_b = server.join("Anna"), server.join("Bernat")
            self.assertEqual(server.write(token_a, "game/state", partida()), 200)
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
