#!/usr/bin/env python3
"""Proves automàtiques del servidor de La Comunitat (sense dependències).

Arranca comunitat.py en una carpeta temporal i comprova, com ho faria un navegador, que:
- es pot entrar, guardar la partida i rebre-la;
- només es poden canviar els documents de la partida (i el nom de cadascú);
- l'historial apunta les partides acabades;
- crear, obrir, duplicar i esborrar partides funciona;
- exportar, importar, les còpies de seguretat i restaurar funcionen;
- el mapa d'exemple i el QR funcionen.

Ús:  python3 build.py && python3 tests/prova_servidor.py
"""
import json
from concurrent.futures import ThreadPoolExecutor
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def partida(**values):
    g = {"v": 2, "hope": 6, "hopeMax": 8, "created": 1, "round": 1, "deck": 50,
         "threat": [2, 2, 3], "threatIdx": 0, "level": "intro", "solo": True,
         "players": [{"name": "Prova"}], "chars": [{"id": "frodosam", "player": 0}],
         "objectives": [{"id": "ring", "name": "Anell", "done": False, "ring": True}],
         "setup": [False], "turn": {"p": 0, "step": 0, "a": [0, 0], "shadow": 0},
         "skies": {"total": 4, "drawn": 0}, "calc": {"naz": 0, "troops": 0, "ring": False,
         "haven": False, "mordor": False, "bKind": "attack", "bFr": 1, "bSh": 1,
         "bNaz": False, "bHaven": False}, "result": None}
    g.update(values)
    return g


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Servidor:
    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="comunitat-prova-"))
        self.port = free_port()
        self.proc = subprocess.Popen(
            [sys.executable, str(ROOT / "comunitat.py"), "--sense-finestra", "--sense-navegador", "--sense-qr",
             "--port", str(self.port), "--dades", str(self.dir), "--partida", "Prova"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        for _ in range(100):
            try:
                self.get("/api/hello")
                return
            except OSError:
                time.sleep(.1)
        self.proc.terminate()
        self.proc.wait(10)
        error = self.proc.stderr.read().decode(errors="replace")
        self.proc.stderr.close()
        shutil.rmtree(self.dir, ignore_errors=True)
        raise RuntimeError("El servidor no arranca: " + error)

    def stop(self):
        self.proc.terminate()
        try:
            self.proc.wait(10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(10)
        self.proc.stderr.close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def req(self, method, path, body=None, tok=None, raw=False, ctype="application/json"):
        data = None if body is None else (body if isinstance(body, bytes) else json.dumps(body).encode())
        r = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data, method=method)
        r.add_header("Content-Type", ctype)
        if tok:
            r.add_header("X-Taula-Token", tok)
        try:
            with urllib.request.urlopen(r, timeout=10) as resp:
                blob = resp.read()
                return resp.status, (blob if raw else json.loads(blob or b"{}")), resp.headers
        except urllib.error.HTTPError as e:
            with e:
                blob = e.read()
            try:
                return e.code, json.loads(blob or b"{}"), e.headers
            except ValueError:
                return e.code, blob, e.headers

    def get(self, path, tok=None, raw=False):
        return self.req("GET", path, tok=tok, raw=raw)

    def post(self, path, body, tok=None, ctype="application/json"):
        return self.req("POST", path, body, tok=tok, ctype=ctype)

    def join(self, name):
        code, d, _ = self.post("/api/join", {"name": name})
        assert code == 200, d
        return d["token"]

    def write(self, tok, path, data, mode="set"):
        if path == "game/state" and mode == "set":
            data = partida(**data)
        _, snap, _ = self.get("/api/snapshot", tok)
        return self.post("/api/write", {"path": path, "mode": mode, "data": data,
                                      "camp": snap["campaign"], "epoch": snap["epoch"], "revision": snap["revision"]}, tok)[0]


class Proves(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s = Servidor()
        cls.tok = cls.s.join("Jugador1")

    @classmethod
    def tearDownClass(cls):
        cls.s.stop()

    def test_01_hola_i_pagina(self):
        code, d, _ = self.s.get("/api/hello")
        self.assertEqual(code, 200)
        self.assertTrue(d["local"])                        # la prova es connecta des del mateix ordinador
        self.assertEqual(Path(d["dades"]).resolve(), self.s.dir.resolve())
        code, page, h = self.s.get("/", raw=True)
        self.assertEqual(code, 200)
        self.assertIn(b"Comunitat", page)

    def test_02_mapa_i_qr(self):
        for lang in ("val", "es"):
            code, img, h = self.s.get(f"/mapa?lang={lang}", raw=True)
            self.assertEqual(code, 200)
            self.assertTrue(img.startswith(b"\xff\xd8"))   # JPEG
        code, d, _ = self.s.get("/api/invite")
        self.assertEqual(code, 200)
        self.assertTrue(d["list"][0]["svg"].startswith("<svg"))

    def test_03_sense_sessio(self):
        self.assertEqual(self.s.get("/api/snapshot")[0], 401)
        self.assertEqual(self.s.post("/api/write", {"path": "game/state", "mode": "set", "data": {}})[0], 401)
        self.assertEqual(self.s.get("/api/export?id=prova")[0], 401)

    def test_04_escriure_i_llegir(self):
        self.assertEqual(self.s.write(self.tok, "game/state", {"v": 2, "hope": 6, "created": 1}), 200)
        self.assertEqual(self.s.write(self.tok, "game/state", {"hope": 5}, "update"), 200)
        code, d, _ = self.s.get("/api/snapshot", self.tok)
        self.assertEqual(d["docs"]["game/state"]["hope"], 5)
        self.assertEqual(d["docs"]["users/" + d["me"]["uid"]]["name"], "Jugador1")

    def test_05_permisos(self):
        self.assertEqual(self.s.write(self.tok, "dm/secret", {"x": 1}), 403)       # fora de la partida
        self.assertEqual(self.s.write(self.tok, "../game/state", {"x": 1}), 400)   # ruta no vàlida
        tok2 = self.s.join("Jugador2")
        code, d, _ = self.s.get("/api/snapshot", self.tok)
        other = next(p for p, v in d["docs"].items() if p.startswith("users/") and v["name"] == "Jugador2")
        self.assertEqual(self.s.write(self.tok, other, {"name": "Intrús"}), 403)  # el nom d'un altre
        self.assertEqual(self.s.write(tok2, other, {"name": "Jugadora2"}), 200)

    def test_06_historial(self):
        self.s.write(self.tok, "game/state", {"v": 2, "created": 7, "result": "win", "level": "intro",
                                            "players": [{"name": "Jugador1"}]})
        code, d, _ = self.s.get("/api/history", self.tok)
        self.assertTrue(any(h["result"] == "win" and h["created"] == 7 for h in d["list"]))
        self.s.write(self.tok, "game/state", {"result": None}, "update")             # desfer la jugada final
        code, d, _ = self.s.get("/api/history", self.tok)
        self.assertFalse(any(h["created"] == 7 for h in d["list"]))

    def test_07_partides(self):
        code, d, _ = self.s.post("/api/campaigns", {"action": "create", "name": "Divendres"}, self.tok)
        self.assertEqual(d["active"], "divendres")
        code, d, _ = self.s.post("/api/campaigns", {"action": "duplicate", "id": "divendres"}, self.tok)
        self.assertIn("divendres-copia", [c["id"] for c in d["list"]])
        code, d, _ = self.s.post("/api/campaigns", {"action": "delete", "id": "divendres"}, self.tok)
        self.assertEqual(code, 400)                                                # no es pot esborrar l'oberta
        code, d, _ = self.s.post("/api/campaigns", {"action": "delete", "id": "divendres-copia"}, self.tok)
        self.assertNotIn("divendres-copia", [c["id"] for c in d["list"]])
        self.assertTrue(any((self.s.dir / "partides" / "esborrades").glob("divendres-copia-*.json")))
        _, trash, _ = self.s.get("/api/campaigns", self.tok)
        deleted = next(c for c in trash["trash"] if c["name"] == "Divendres (còpia)")
        code, restored, _ = self.s.post("/api/campaigns", {"action": "undelete", "id": deleted["id"]}, self.tok)
        self.assertEqual(code, 200)
        self.assertIn("Divendres (còpia)", [c["name"] for c in restored["list"]])
        self.assertEqual(self.s.post("/api/campaigns", {"action": "undelete", "id": "../prova"}, self.tok)[0], 400)
        code, d, _ = self.s.post("/api/campaigns", {"action": "switch", "id": "prova"}, self.tok)
        self.assertEqual(d["active"], "prova")

    def test_08_exportar_i_importar(self):
        self.s.write(self.tok, "game/state", {"v": 2, "hope": 3, "created": 9})
        code, blob, h = self.s.get("/api/export?id=prova", self.tok, raw=True)
        self.assertEqual(code, 200)
        self.assertIn("attachment", h["Content-Disposition"])
        info = json.loads(blob)
        self.assertEqual(info["format"], "comunitat-del-anell")
        self.assertEqual(info["docs"]["game/state"]["hope"], 3)
        code, d, _ = self.s.post("/api/import", blob, self.tok)
        self.assertEqual(code, 200, d)
        nova = d["imported"]
        self.assertNotEqual(nova, "prova")
        self.assertIn("(importada)", next(c["name"] for c in d["list"] if c["id"] == nova))
        doc = json.loads((self.s.dir / "partides" / f"{nova}.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["docs"]["game/state"]["hope"], 3)
        # Un fitxer que no és una partida, o amb documents de fora, es rebutja
        self.assertEqual(self.s.post("/api/import", b"no es json", self.tok)[0], 400)
        dolent = json.dumps({"docs": {"users/u1": {"name": "x"}}}).encode()
        self.assertEqual(self.s.post("/api/import", dolent, self.tok)[0], 400)

    def test_09_copies_i_restaurar(self):
        self.s.write(self.tok, "game/state", {"v": 2, "hope": 4, "created": 11})
        code, d, _ = self.s.post("/api/campaigns", {"action": "backup", "id": "prova"}, self.tok)
        self.assertEqual(code, 200)
        copia = next(b for b in d["list"] if b["reason"] == "ma")
        self.s.write(self.tok, "game/state", {"v": 2, "hope": 1, "created": 11})
        code, d, _ = self.s.post("/api/campaigns", {"action": "restore", "id": "prova", "backup": copia["id"]}, self.tok)
        self.assertEqual(code, 200, d)
        code, d, _ = self.s.get("/api/snapshot", self.tok)
        self.assertEqual(d["docs"]["game/state"]["hope"], 4)
        code, d, _ = self.s.post("/api/campaigns", {"action": "backups", "id": "prova"}, self.tok)
        self.assertTrue(any(b["reason"] == "abans" for b in d["list"]))           # el que hi havia abans de restaurar
        code, d, _ = self.s.post("/api/campaigns", {"action": "restore", "id": "prova", "backup": "../../x"}, self.tok)
        self.assertEqual(code, 404)

    def test_10_conflicte_i_transaccio(self):
        _, snap, _ = self.s.get("/api/snapshot", self.tok)
        def transaction(hope, request_id):
            return {"camp": snap["campaign"], "epoch": snap["epoch"], "revision": snap["revision"], "requestId": request_id,
                    "changes": [{"path": "game/state", "data": partida(hope=hope)},
                                {"path": "game/log", "data": {"list": [{"k": request_id}]}},
                                {"path": "game/undo", "data": {"stack": []}}]}
        a, b = transaction(5, "jugador-a"), transaction(2, "jugador-b")
        tok2 = self.s.join("Simultani")
        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(self.s.post, "/api/transaction", a, self.tok)
            second = pool.submit(self.s.post, "/api/transaction", b, tok2)
            results = [first.result(), second.result()]
        self.assertEqual(sorted(r[0] for r in results), [200, 409])
        winner = 0 if results[0][0] == 200 else 1
        request, token = (a, self.tok) if winner == 0 else (b, tok2)
        _, saved, _ = self.s.get("/api/snapshot", self.tok)
        self.assertEqual(saved["docs"]["game/state"]["hope"], 5 if winner == 0 else 2)
        self.assertEqual(saved["docs"]["game/log"]["list"][0]["k"], request["requestId"])
        self.assertEqual(saved["docs"]["game/undo"], {"stack": []})
        disk = json.loads((self.s.dir / "partides" / (snap["campaign"] + ".json")).read_text(encoding="utf-8"))
        self.assertEqual(disk["docs"]["game/state"], saved["docs"]["game/state"])
        code, retried, _ = self.s.post("/api/transaction", request, token)
        self.assertEqual(code, 200)
        self.assertEqual(retried["revision"], saved["revision"])

    def test_11_importacions_incorrectes(self):
        for key, value in (("hope", -1), ("hope", True), ("players", "x"),
                           ("threat", []), ("turn", {}), ("v", 99), ("calc", None)):
            with self.subTest(key=key, value=value):
                info = {"docs": {"game/state": partida(**{key: value})}}
                self.assertEqual(self.s.post("/api/import", info, self.tok)[0], 400)
        self.assertEqual(self.s.post("/api/import", {"format": "altre", "versio": 1, "docs": {}}, self.tok)[0], 400)
        self.assertEqual(self.s.post("/api/join", [], self.tok)[0], 400)

    def test_12_transaccio_invalida_no_canvia_res(self):
        _, before, _ = self.s.get("/api/snapshot", self.tok)
        body = {"camp": before["campaign"], "epoch": before["epoch"], "revision": before["revision"], "requestId": "invalid",
                "changes": [{"path": "game/log", "data": {"list": [{"k": "no guardar"}]}},
                            {"path": "game/state", "data": partida(hope=999)}]}
        self.assertEqual(self.s.post("/api/transaction", body, self.tok)[0], 400)
        _, after, _ = self.s.get("/api/snapshot", self.tok)
        self.assertEqual(before, after)

    def test_13_revisio_abans_de_reiniciar(self):
        _, before, _ = self.s.get("/api/snapshot", self.tok)
        body = {"camp": before["campaign"], "epoch": "servidor-anterior", "revision": before["revision"],
                "requestId": "antic", "changes": [{"path": "game/state", "data": partida(hope=1)}]}
        self.assertEqual(self.s.post("/api/transaction", body, self.tok)[0], 409)
        _, after, _ = self.s.get("/api/snapshot", self.tok)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main(verbosity=2)
