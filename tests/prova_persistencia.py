# SPDX-License-Identifier: GPL-3.0-or-later
"""Proves de l'escriptura segura, el bloqueig de la carpeta i el pas de les dades de la v2 a la v3.
Només fan servir carpetes temporals.

Ús:  python3 build.py && python3 tests/prova_persistencia.py
"""
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.persistencia import DataDirectoryLock, atomic_json, migra_v2  # noqa: E402


def sqlite_v2(directory, body, pending=1):
    """Una carpeta de dades com les de la v2.7: comunitat.sqlite3 amb l'última foto de tot."""
    with sqlite3.connect(str(directory / "comunitat.sqlite3")) as db:
        db.execute("CREATE TABLE snapshot (id INTEGER PRIMARY KEY CHECK (id = 1), body TEXT NOT NULL, pending INTEGER NOT NULL)")
        db.execute("INSERT INTO snapshot VALUES (1, ?, ?)", (json.dumps(body), pending))
    db.close()


class Persistencia(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.dir = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_atomic_json(self):
        f = self.dir / "partides" / "a.json"
        atomic_json(f, {"nom": "àèí"})
        self.assertEqual(json.loads(f.read_text(encoding="utf-8")), {"nom": "àèí"})
        # Si falla a mitjan escriure, el fitxer d'abans queda sencer i no queden temporals
        with patch("json.dump", side_effect=OSError("disc ple")):
            with self.assertRaises(OSError):
                atomic_json(f, {"nom": "nou"})
        self.assertEqual(json.loads(f.read_text(encoding="utf-8")), {"nom": "àèí"})
        self.assertEqual(sorted(p.name for p in f.parent.iterdir()), ["a.json"])
        with self.assertRaises(ValueError):
            atomic_json(f, {"x": float("nan")})

    def test_bloqueig(self):
        primer = DataDirectoryLock(self.dir)
        with self.assertRaises(OSError):
            DataDirectoryLock(self.dir)
        primer.close()
        DataDirectoryLock(self.dir).close()

    def test_migra_foto_pendent(self):
        """La v2 va tancar abans d'escriure els JSON: s'escriuen ara des de la base de dades."""
        docs = {"campaign/main": {"name": "Divendres"}, "game/state": {"hope": 3}}
        sqlite_v2(self.dir, {"meta": {"active": "divendres", "users": {"u1": {"name": "Jugador1"}}, "pin": "1234"},
                             "docs": docs, "history": [{"id": "divendres:1", "result": "win"}]})
        migra_v2(self.dir)
        self.assertEqual(json.loads((self.dir / "partides/divendres.json").read_text(encoding="utf-8")), {"docs": docs})
        self.assertEqual(json.loads((self.dir / "historial.json").read_text(encoding="utf-8"))["list"][0]["result"], "win")
        self.assertEqual(json.loads((self.dir / "comunitat.json").read_text(encoding="utf-8")), {"versio": 3, "active": "divendres"})
        self.assertFalse((self.dir / "comunitat.sqlite3").exists())
        self.assertTrue((self.dir / "copies/v2/comunitat.sqlite3").exists())
        migra_v2(self.dir)   # la segona vegada no fa res
        self.assertTrue((self.dir / "partides/divendres.json").exists())

    def test_migra_sense_res_pendent(self):
        """Si els JSON ja estaven al dia, no es toquen; de comunitat.json es lleva el que era de la sala."""
        atomic_json(self.dir / "partides/a.json", {"docs": {"campaign/main": {"name": "Nou"}}})
        atomic_json(self.dir / "comunitat.json", {"active": "a", "users": {"u1": {"name": "Jugador1"}},
                                                  "sessions": {"t": {"uid": "u1"}}, "pin": "1234"})
        sqlite_v2(self.dir, {"meta": {"active": "a"}, "docs": {"campaign/main": {"name": "Vell"}}, "history": []}, pending=0)
        migra_v2(self.dir)
        self.assertEqual(json.loads((self.dir / "partides/a.json").read_text(encoding="utf-8"))["docs"]["campaign/main"]["name"], "Nou")
        self.assertEqual(json.loads((self.dir / "comunitat.json").read_text(encoding="utf-8")), {"versio": 3, "active": "a"})
        self.assertTrue((self.dir / "copies/v2/comunitat.sqlite3").exists())

    def test_migra_base_de_dades_danyada(self):
        (self.dir / "comunitat.sqlite3").write_bytes(b"no es sqlite")
        atomic_json(self.dir / "partides/a.json", {"docs": {}})
        migra_v2(self.dir)
        self.assertTrue((self.dir / "partides/a.json").exists())
        self.assertTrue((self.dir / "copies/v2/comunitat.sqlite3").exists())

    def test_programa_obri_dades_v2(self):
        """El programa sencer arranca sobre una carpeta de la v2 i la deixa a punt."""
        sqlite_v2(self.dir, {"meta": {"active": "a", "users": {}}, "docs": {"campaign/main": {"name": "A"}}, "history": []})
        sys.path.insert(0, str(ROOT / "tests"))
        from prova_servidor import Programa
        p = Programa(self.dir)
        try:
            self.assertEqual(p.get("/api/hola")[0], 200)
            self.assertEqual(p.disc("llig", ruta="comunitat.json")[1]["obj"], {"versio": 3, "active": "a"})
        finally:
            p.tanca()
        self.assertTrue((self.dir / "partides/a.json").exists())
        self.assertFalse((self.dir / "comunitat.sqlite3").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
