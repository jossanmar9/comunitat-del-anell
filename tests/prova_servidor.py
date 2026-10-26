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
    def __init__(self, wanted="Prova"):
        self.dir = Path(tempfile.mkdtemp(prefix="comunitat-prova-"))
        self.port = free_port()
        self.proc = subprocess.Popen(
            [sys.executable, str(ROOT / "comunitat.py"), "--sense-finestra", "--sense-navegador", "--sense-qr",
             "--port", str(self.port), "--dades", str(self.dir), *(["--partida", wanted] if wanted else [])],
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

    def master(self):
        return self.post("/api/join", {"master": True})[1]["token"]

    def create_player(self, name, race="home"):
        code, d, _ = self.post("/api/players", {"action": "create", "name": name, "race": race}, self.master())
        assert code == 200, d
        return d

    def join(self, name):
        player = self.create_player(name)
        code, d, _ = self.post("/api/join", {"uid": player["uid"], "pin": player["pin"]})
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
        cls.tok = cls.s.master()

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
        self.assertTrue(d["me"]["dm"])

    def test_05_permisos(self):
        self.assertEqual(self.s.write(self.tok, "dm/secret", {"x": 1}), 403)       # fora de la partida
        self.assertEqual(self.s.write(self.tok, "../game/state", {"x": 1}), 400)   # ruta no vàlida
        tok2 = self.s.join("Jugador2")
        code, d, _ = self.s.get("/api/snapshot", self.tok)
        other = next(p for p, v in d["docs"].items() if p.startswith("users/") and v["name"] == "Jugador2")
        self.assertEqual(self.s.write(self.tok, other, {"name": "Intrús"}), 403)  # el nom d'un altre
        self.assertEqual(self.s.write(tok2, other, {"name": "Jugadora2"}), 403)

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
        tok2 = self.s.join("Simultani")
        _, snap, _ = self.s.get("/api/snapshot", self.tok)
        def transaction(hope, request_id):
            return {"camp": snap["campaign"], "epoch": snap["epoch"], "revision": snap["revision"], "requestId": request_id,
                    "changes": [{"path": "game/state", "data": partida(hope=hope, players=snap["docs"]["game/state"]["players"])},
                                {"path": "game/log", "data": {"list": [{"k": request_id}]}},
                                {"path": "game/undo", "data": {"stack": []}}]}
        a, b = transaction(5, "jugador-a"), transaction(2, "jugador-b")
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


class Sala(unittest.TestCase):
    def setUp(self):
        self.s = Servidor()
        self.master = self.s.master()

    def tearDown(self):
        self.s.stop()

    def admin(self, **body):
        return self.s.post("/api/players", body, self.master)

    def test_identitat_pin_sessions_i_permisos(self):
        code, u, _ = self.admin(action="create", name="  Jósé   Pla ", race="elf")
        self.assertEqual(code, 200)
        uid, pin = u["uid"], u["pin"]
        self.assertRegex(pin, r"^[0-9]{4}$")
        self.assertEqual(self.admin(action="create", name="JOSE PLA", race="home")[0], 409)
        self.assertEqual(self.admin(action="create", uid=uid, name="Jose Pla", race="home")[0], 409)
        self.assertEqual(self.admin(action="create", name="Invalid", race=[])[0], 400)
        self.assertEqual(self.s.post("/api/join", {"name": "Lliure"})[0], 403)
        wrong_pin = f"{(int(pin) + 1) % 10000:04d}"
        self.assertEqual(self.s.post("/api/join", {"uid": uid, "pin": wrong_pin})[0], 403)
        code, joined, _ = self.s.post("/api/join", {"uid": uid, "pin": pin})
        self.assertEqual(code, 200)
        tok = joined["token"]
        self.assertFalse(joined["dm"])
        self.assertEqual(self.s.post("/api/join", {"uid": uid, "pin": pin})[0], 409)
        self.assertEqual(self.s.post("/api/join", {"token": tok})[1]["token"], tok)
        self.assertEqual(self.s.post("/api/players", {"action": "delete", "uid": uid}, tok)[0], 403)
        self.assertEqual(self.s.post("/api/campaigns", {"action": "create", "name": "Intrus"}, tok)[0], 403)
        self.assertEqual(self.s.post("/api/import", {"docs": {}}, tok)[0], 403)
        self.assertEqual(self.s.write(tok, "users/" + uid, {"name": "intrus"}), 403)
        public = self.s.get("/api/players")[1]
        self.assertNotIn(uid, [p["uid"] for p in public["list"]])
        snapshot = self.s.get("/api/snapshot", tok)[1]
        self.assertNotIn("pin", snapshot["docs"]["users/" + uid])
        old_alias = snapshot["docs"]["users/" + uid]["alias"]
        _, edited, _ = self.admin(action="edit", uid=uid, name="Josep", race="nan")
        new = next(p for p in edited["list"] if p["uid"] == uid)
        self.assertNotEqual(new["alias"], old_alias)
        self.assertEqual(new["race"], "nan")
        self.admin(action="lock", open=False)
        self.assertEqual(self.s.post("/api/join", {"token": tok})[0], 200)
        self.admin(action="revoke", uid=uid)
        self.assertEqual(self.s.get("/api/snapshot", tok)[0], 401)
        self.assertEqual(self.s.post("/api/join", {"uid": uid, "pin": pin})[0], 403)
        self.admin(action="lock", open=True)
        _, reset, _ = self.admin(action="pin", uid=uid)
        self.assertEqual(self.s.post("/api/join", {"uid": uid, "pin": reset["pin"]})[0], 200)
        token_after_reset = next(iter(json.loads((self.s.dir / "comunitat.json").read_text())["sessions"]))
        _, second_reset, _ = self.admin(action="pin", uid=uid)
        self.assertEqual(self.s.get("/api/snapshot", token_after_reset)[0], 401)
        if second_reset["pin"] != reset["pin"]:
            self.assertEqual(self.s.post("/api/join", {"uid": uid, "pin": reset["pin"]})[0], 403)
        persisted = json.loads((self.s.dir / "comunitat.json").read_text())
        self.assertIsInstance(persisted["users"][uid]["pin"], dict)
        self.assertNotIn('"pin": "', json.dumps(persisted))
        self.admin(action="delete", uid=uid)
        self.assertNotIn(uid, [u["uid"] for u in self.s.get("/api/players", self.master)[1]["list"]])

    def test_master_local_i_origen(self):
        import urllib.request
        for headers in ({"Host": "evil.example"}, {"Origin": "http://evil.example"}, {"Sec-Fetch-Site": "cross-site"}):
            req = urllib.request.Request(f"http://127.0.0.1:{self.s.port}/api/join", data=b'{"master":true}', headers={"Content-Type": "application/json", **headers})
            with self.assertRaises(urllib.error.HTTPError) as error:
                urllib.request.urlopen(req, timeout=5)
            self.assertEqual(error.exception.code, 403)
            error.exception.close()

    def test_crear_partida_i_recuperar_jugadors(self):
        def setup(players, request_id):
            snap = self.s.get("/api/snapshot", self.master)[1]
            game = partida(players=players)
            return self.s.post("/api/setup", {"game": game, "name": "Partida amb sala", "requestId": request_id,
                "camp": snap["campaign"], "epoch": snap["epoch"], "revision": snap["revision"]}, self.master)
        snap = self.s.get("/api/snapshot", self.master)[1]
        player_token = self.s.join("Sense permisos")
        self.assertEqual(self.s.post("/api/setup", {}, player_token)[0], 403)
        count = len(self.s.get("/api/players", self.master)[1]["list"])
        self.assertEqual(setup([{"name": "Ànna", "race": "elf"}, {"name": " ANNA ", "race": "home"}], "duplicate")[0], 409)
        self.assertEqual(len(self.s.get("/api/players", self.master)[1]["list"]), count)
        code, created, _ = setup([{"name": "Anna nova", "race": "elf"}], "create-roster")
        self.assertEqual(code, 200)
        self.assertEqual(len(created["pins"]), 1)
        participant = created["snapshot"]["docs"]["game/state"]["players"][0]
        uid, pin = participant["uid"], created["pins"][0]["pin"]
        code, joined, _ = self.s.post("/api/join", {"uid": uid, "pin": pin})
        self.assertEqual(code, 200)
        changed = created["snapshot"]["docs"]["game/state"].copy()
        changed["players"] = [{**participant, "name": "Intrus"}]
        self.assertEqual(self.s.write(joined["token"], "game/state", changed), 403)
        code, reused, _ = setup([{"name": "ANNA NOVA", "race": "elf"}], "reuse-roster")
        self.assertEqual(code, 200)
        self.assertEqual(reused["pins"], [])
        self.assertEqual(reused["snapshot"]["docs"]["game/state"]["players"][0]["uid"], uid)
        self.s.post("/api/campaigns", {"action": "create", "name": "Altra"}, self.master)
        self.s.post("/api/players", {"action": "delete", "uid": uid}, self.master)
        code, _, _ = self.s.post("/api/campaigns", {"action": "switch", "id": snap["campaign"]}, self.master)
        self.assertEqual(code, 200)
        roster = self.s.get("/api/players", self.master)[1]["list"]
        recovered = next(u for u in roster if u["uid"] == uid)
        self.assertEqual(recovered["alias"], participant["alias"])
        self.assertEqual(recovered["alias_gender"], participant["alias_gender"])
        self.assertFalse(recovered["pin_ready"])

    def test_arrancada_sense_partida(self):
        other = Servidor(wanted=None)
        try:
            token = other.master()
            snapshot = other.get("/api/snapshot", token)[1]
            self.assertIsNone(snapshot["campaign"])
            self.assertEqual(snapshot["docs"], {})
            self.assertEqual(list((other.dir / "partides").glob("*.json")), [])
            self.assertEqual(other.write(token, "game/state", partida()), 403)
            code, result, _ = other.post("/api/setup", {"game": partida(players=[{"name": "Primer", "race": "nan"}]),
                "name": "Des de zero", "requestId": "first", "epoch": snapshot["epoch"], "revision": snapshot["revision"], "camp": None}, token)
            self.assertEqual(code, 200)
            self.assertEqual(result["snapshot"]["campaign"], "des-de-zero")
            self.assertEqual(len(result["pins"]), 1)
        finally:
            other.stop()

    def test_alias_masculi_femeni_i_correccio(self):
        cases = [("José", "male"), ("Núria", "female"), ("Maria José", "female"),
                 ("Josep Maria", "male"), ("Àlex", "neutral"), ("Nom desconegut", "neutral")]
        from urllib.parse import quote
        for name, gender in cases:
            self.assertEqual(self.s.get("/api/alias-gender?name=" + quote(name), self.master)[1]["alias_gender"], gender)
        code, created, _ = self.admin(action="create", name="Núria", race="nan")
        self.assertEqual(code, 200)
        uid = created["uid"]
        female = next(u for u in created["list"] if u["uid"] == uid)
        self.assertEqual(female["alias_gender"], "female")
        self.assertIn(female["alias"].split()[0], ("Drevuka", "Zavruna", "Kelvuda", "Pravneka", "Veskuda", "Drumveka"))
        persisted = json.loads((self.s.dir / "comunitat.json").read_text())["users"][uid]
        pin_record = persisted["pin"]
        code, edited, _ = self.admin(action="edit", uid=uid, name="Núria", race="nan", alias_gender="male")
        self.assertEqual(code, 200)
        male = next(u for u in edited["list"] if u["uid"] == uid)
        self.assertEqual(male["alias_gender"], "male")
        self.assertNotEqual(male["alias"], female["alias"])
        self.assertEqual(json.loads((self.s.dir / "comunitat.json").read_text())["users"][uid]["pin"], pin_record)
        self.assertEqual(self.admin(action="edit", uid=uid, name="Núria", race="nan", alias_gender="invalid")[0], 400)
        # Preferència manual: en reanomenar no es torna a deduir.
        _, renamed, _ = self.admin(action="edit", uid=uid, name="Maria", race="nan")
        self.assertEqual(next(u for u in renamed["list"] if u["uid"] == uid)["alias"], male["alias"])
        # La preparació automàtica d'una altra partida respecta la correcció guardada.
        snap = self.s.get("/api/snapshot", self.master)[1]
        code, setup, _ = self.s.post("/api/setup", {"game": partida(players=[{"name": "Maria", "race": "nan", "alias_gender": "auto"}]),
            "name": "Preferència", "requestId": "manual-gender", "camp": snap["campaign"], "epoch": snap["epoch"], "revision": snap["revision"]}, self.master)
        self.assertEqual(code, 200)
        self.assertEqual(setup["snapshot"]["docs"]["game/state"]["players"][0]["alias_gender"], "male")
        self.assertEqual(setup["snapshot"]["docs"]["game/state"]["players"][0]["alias"], male["alias"])


    def test_reinici_des_pres_de_tancament_forcat(self):
        snap = self.s.get("/api/snapshot", self.master)[1]
        code, created, _ = self.s.post("/api/setup", {"game": partida(players=[{"name": "Reinici", "race": "elf"}]),
            "name": "Durable", "requestId": "crash-setup", "camp": snap["campaign"], "epoch": snap["epoch"], "revision": snap["revision"]}, self.master)
        self.assertEqual(code, 200)
        uid = created["pins"][0]["uid"]
        pin = created["pins"][0]["pin"]
        code, joined, _ = self.s.post("/api/join", {"uid": uid, "pin": pin})
        self.assertEqual(code, 200)
        game = created["snapshot"]["docs"]["game/state"]
        self.assertEqual(self.s.write(self.master, "game/state", {**game, "hope": 3, "result": "win"}), 200)
        # Sense SIGTERM ni guardat de tancament: equival al procés interromput.
        self.s.proc.kill()
        self.s.proc.wait(10)
        self.s.proc.stderr.close()
        for path in (self.s.dir / "comunitat.json", self.s.dir / "historial.json", self.s.dir / "partides/prova.json"):
            path.write_text("incomplete mirror")
        self.s.proc = subprocess.Popen([sys.executable, str(ROOT / "comunitat.py"), "--sense-finestra", "--sense-navegador", "--sense-qr",
            "--port", str(self.s.port), "--dades", str(self.s.dir)], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        for _ in range(100):
            try:
                if self.s.get("/api/hello")[0] == 200:
                    break
            except OSError:
                time.sleep(.1)
        master = self.s.master()
        self.assertIsNone(self.s.get("/api/snapshot", master)[1]["campaign"])
        self.assertEqual(self.s.post("/api/join", {"token": joined["token"]})[0], 200)
        self.assertEqual(self.s.post("/api/campaigns", {"action": "switch", "id": "prova"}, master)[0], 200)
        recovered = self.s.get("/api/snapshot", joined["token"])[1]["docs"]["game/state"]
        self.assertEqual(recovered["hope"], 3)
        self.assertEqual(recovered["players"][0]["uid"], uid)
        self.assertTrue(any(h["result"] == "win" for h in self.s.get("/api/history", master)[1]["list"]))

    def test_rate_limit(self):
        u = self.s.create_player("Intents")
        for _ in range(5):
            self.assertEqual(self.s.post("/api/join", {"uid": u["uid"], "pin": "bad"})[0], 403)
        self.assertEqual(self.s.post("/api/join", {"uid": u["uid"], "pin": u["pin"]})[0], 429)
        # El màster encara pot administrar la sala.
        self.assertEqual(self.admin(action="pin", uid=u["uid"])[0], 200)

    def test_alias_unics(self):
        aliases = set()
        for i in range(20):
            d = self.s.create_player("Alias " + str(i), ["home", "elf", "nan", "hobbit"][i % 4])
            u = next(u for u in d["list"] if u["uid"] == d["uid"])
            self.assertNotIn(u["alias"], aliases)
            aliases.add(u["alias"])

    def test_migracio_i_reinici(self):
        # Executa les funcions reals del mòdul generat amb dades temporals.
        import importlib.util
        spec = importlib.util.spec_from_file_location("comunitat_migration", ROOT / "comunitat.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as folder:
            module.set_data_dir(folder)
            module.DATA_DIR.mkdir(exist_ok=True)
            module.CAMP_DIR.mkdir()
            legacy_docs = {"campaign/main": {"name": "Llegat"}, "game/state": partida(hope=4)}
            module.write_json(module.camp_file("legacy"), {"docs": legacy_docs})
            module.write_json(module.META, {"active": "legacy", "users": {"old": "Ànna", "dict": {"name": "ANNA", "alias": "Bungo", "race": "hobbit"}},
                                          "sessions": {"insecure": {"uid": "old", "dm": True}}})
            module.load("legacy")
            self.assertEqual(module.state["docs"]["game/state"]["hope"], legacy_docs["game/state"]["hope"])
            self.assertTrue({"old", "dict"}.issubset(module.state["users"]))
            self.assertNotEqual(module.state["users"]["old"]["name"], module.state["users"]["dict"]["name"])
            self.assertEqual(module.state["sessions"], {})
            self.assertNotEqual(module.state["users"]["dict"]["alias"], "Bungo")
            module.set_pin(module.state["users"]["old"])
            module.state["sessions"]["secure"] = {"uid": "old", "dm": False, "auth_version": 2}
            module.state["connections_open"] = False
            module.save_now()
            before = module.state["users"].copy()
            module.load()
            self.assertEqual(module.state["users"], before)
            self.assertIsNone(module.state["active"])
            self.assertEqual(module.state["docs"], {})
            self.assertTrue(module.camp_file("legacy").exists())
            self.assertIn("secure", module.state["sessions"])
            self.assertFalse(module.state["connections_open"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
