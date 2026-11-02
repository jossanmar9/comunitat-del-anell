#!/usr/bin/env python3
"""Proves automàtiques del programa d'escriptori (sense dependències).

Arranca comunitat.py en una carpeta temporal i comprova que:
- serveix l'app, el mapa d'exemple i /api/hola;
- el «disc» (llegir, escriure, llistar, esborrar i moure fitxers JSON) funciona i només deixa
  tocar els fitxers de dades de La Comunitat;
- només accepta peticions d'aquest ordinador i de la mateixa app;
- un fitxer danyat es guarda a part i no es perd;
- no es pot obrir dues vegades la mateixa carpeta de dades;
- les partides exportades van a Baixades sense sobreescriure res.

Ús:  python3 build.py && python3 tests/prova_servidor.py
"""
import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def port_lliure():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Programa:
    def __init__(self, dades, home=None):
        self.port = port_lliure()
        env = dict(os.environ)
        if home:
            env["HOME"] = str(home)
        self.proc = subprocess.Popen(
            [sys.executable, str(ROOT / "comunitat.py"), "--sense-finestra", "--sense-navegador",
             "--port", str(self.port), "--dades", str(dades)],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
        for _ in range(100):
            try:
                if self.get("/api/hola")[0] == 200:
                    return
            except OSError:
                pass
            if self.proc.poll() is not None:
                return
            time.sleep(0.1)
        raise RuntimeError("El programa no ha arrancat")

    def peticio(self, metode, cami, cos=None, capcaleres=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        h = {"Host": f"127.0.0.1:{self.port}"}
        if cos is not None:
            h.update({"Content-Type": "application/json", "X-Comunitat": "1"})
        h.update(capcaleres or {})
        c.request(metode, cami, body=None if cos is None else json.dumps(cos).encode(), headers=h)
        r = c.getresponse()
        dades = r.read()
        c.close()
        try:
            dades = json.loads(dades)
        except ValueError:
            pass
        return r.status, dades, r

    def get(self, cami, **kw):
        return self.peticio("GET", cami, **kw)

    def disc(self, op, **cos):
        return self.peticio("POST", "/api/disc", {"op": op, **cos})

    def tanca(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(10)
        eixida = self.proc.stdout.read().decode("utf-8", "replace")
        self.proc.stdout.close()
        return eixida


class Servidor(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="comunitat-prova-"))
        self.dades = self.dir / "dades"
        self.home = self.dir / "home"
        (self.home / "Downloads").mkdir(parents=True)
        self.p = Programa(self.dades, self.home)

    def tearDown(self):
        self.p.tanca()
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_pagina_mapa_i_hola(self):
        s, d, r = self.p.get("/")
        self.assertEqual(s, 200)
        self.assertIn('const ENTORN="escriptori"', d.decode("utf-8") if isinstance(d, bytes) else d)
        self.assertIn("frame-ancestors 'none'", r.getheader("Content-Security-Policy"))
        for lang in ("val", "es"):
            s, d, r = self.p.get("/mapa?lang=" + lang)
            self.assertEqual(s, 200)
            self.assertEqual(r.getheader("Content-Type"), "image/jpeg")
        s, d, _ = self.p.get("/api/hola")
        self.assertEqual(d["comunitat"], 3)
        self.assertEqual(Path(d["dades"]).resolve(), self.dades.resolve())
        self.assertEqual(self.p.get("/no-hi-ha")[0], 404)

    def test_disc(self):
        doc = {"docs": {"campaign/main": {"name": "Divendres àèí"}}}
        self.assertEqual(self.p.disc("llig", ruta="partides/a.json")[1], {"obj": None})
        self.assertEqual(self.p.disc("escriu", ruta="partides/a.json", obj=doc)[0], 200)
        self.assertEqual(self.p.disc("llig", ruta="partides/a.json")[1]["obj"], doc)
        self.assertEqual(json.loads((self.dades / "partides" / "a.json").read_text(encoding="utf-8")), doc)
        llista = self.p.disc("llista", carpeta="partides")[1]["list"]
        self.assertEqual([f["nom"] for f in llista], ["a.json"])
        self.assertIsInstance(llista[0]["ts"], int)
        self.assertEqual(self.p.disc("llista", carpeta="copies/a")[1], {"list": []})
        # Moure (esborrar una partida la mou a la paperera)
        self.assertEqual(self.p.disc("mou", ruta="partides/a.json", a="partides/esborrades/a-1.json")[0], 200)
        self.assertEqual(self.p.disc("llista", carpeta="partides")[1]["list"], [])
        s, d, _ = self.p.disc("mou", ruta="partides/a.json", a="partides/b.json")
        self.assertEqual((s, d["error"]), (400, "Aquesta partida ja no existeix."))
        self.p.disc("escriu", ruta="partides/b.json", obj=doc)
        self.p.disc("escriu", ruta="partides/c.json", obj=doc)
        s, d, _ = self.p.disc("mou", ruta="partides/b.json", a="partides/c.json")
        self.assertEqual((s, d["error"]), (400, "Ja hi ha una partida amb aquest nom."))
        self.assertEqual(self.p.disc("esborra", ruta="partides/b.json")[0], 200)
        self.assertFalse((self.dades / "partides" / "b.json").exists())
        for f in ("historial.json", "comunitat.json", "mapa.json", "copies/c/20260101-120000-ma.json"):
            self.assertEqual(self.p.disc("escriu", ruta=f, obj={"list": []})[0], 200, f)

    def test_rutes_no_valides(self):
        for ruta in ("../fora.json", "partides/../../fora.json", "/etc/passwd", "partides/a.txt", "partides\\a.json",
                     "copies/../a.json", "partides/A.json", "partides/.json", "altres/a.json", "comunitat.lock", 5, None):
            s, d, _ = self.p.disc("escriu", ruta=ruta, obj={})
            self.assertEqual((s, d.get("error")), (400, "Ruta no vàlida."), ruta)
        self.assertEqual(self.p.disc("llista", carpeta="..")[0], 400)
        self.assertEqual(self.p.disc("llista", carpeta="partides/x")[0], 400)
        self.assertEqual(self.p.disc("escriu", ruta="partides/a.json", obj="text")[0], 400)
        self.assertEqual(self.p.disc("formata")[1]["error"], "Acció desconeguda.")
        self.assertFalse((self.dir / "fora.json").exists())

    def test_nomes_aquest_ordinador_i_aquesta_app(self):
        cos = {"op": "llista", "carpeta": "partides"}
        # Sense la capçalera de l'app (una altra web no la pot posar sense permís)
        s, d, _ = self.p.peticio("POST", "/api/disc", cos, {"X-Comunitat": "0"})
        self.assertEqual(s, 403)
        # Un altre nom (atac de DNS rebinding)
        for host in ("dolent.example:%d" % self.p.port, "127.0.0.1:1", "localhost"):
            self.assertEqual(self.p.peticio("POST", "/api/disc", cos, {"Host": host})[0], 403, host)
            self.assertEqual(self.p.get("/", capcaleres={"Host": host})[0], 403, host)
        self.assertEqual(self.p.peticio("POST", "/api/disc", cos, {"Host": f"localhost:{self.p.port}"})[0], 200)
        # Cos mal format o massa gran
        c = http.client.HTTPConnection("127.0.0.1", self.p.port, timeout=10)
        c.request("POST", "/api/disc", body=b"[1,2]", headers={"X-Comunitat": "1", "Content-Type": "application/json"})
        self.assertEqual(c.getresponse().status, 400)
        c.close()
        c = http.client.HTTPConnection("127.0.0.1", self.p.port, timeout=10)
        c.putrequest("POST", "/api/disc")
        c.putheader("X-Comunitat", "1")
        c.putheader("Content-Length", str(200 * 1024 * 1024))
        c.endheaders()
        self.assertEqual(c.getresponse().status, 413)
        c.close()

    def test_fitxer_danyat(self):
        (self.dades / "partides").mkdir(parents=True, exist_ok=True)
        (self.dades / "partides" / "mal.json").write_text("{no és json", encoding="utf-8")
        self.assertEqual(self.p.disc("llig", ruta="partides/mal.json")[1], {"obj": None})
        self.assertTrue((self.dades / "partides" / "mal.json.danyat").exists())
        self.assertEqual(self.p.disc("llista", carpeta="partides")[1]["list"], [])

    def test_una_sola_vegada(self):
        segon = Programa(self.dades)
        segon.proc.wait(20)
        eixida = segon.tanca()
        self.assertNotEqual(segon.proc.returncode, 0)
        self.assertIn("ja està oberta", eixida)

    @unittest.skipIf(os.name == "nt", "a Windows, Baixades és la de l'usuari de veritat")
    def test_exportar_a_baixades(self):
        s, d, _ = self.p.peticio("POST", "/api/desa", {"nom": "divendres-20261030.json", "text": "{\"a\":1}"})
        self.assertEqual(s, 200)
        primer = Path(d["cami"])
        self.assertEqual(primer.read_text(encoding="utf-8"), "{\"a\":1}")
        s, d, _ = self.p.peticio("POST", "/api/desa", {"nom": "divendres-20261030.json", "text": "{}"})
        self.assertEqual(Path(d["cami"]).name, "divendres-20261030 (2).json")
        self.assertEqual(primer.read_text(encoding="utf-8"), "{\"a\":1}")
        for nom in ("../fora.json", "a.exe", "", None):
            self.assertEqual(self.p.peticio("POST", "/api/desa", {"nom": nom, "text": "{}"})[0], 400, nom)


if __name__ == "__main__":
    unittest.main(verbosity=2)
