# SPDX-License-Identifier: GPL-3.0-or-later
"""Proves de fallades, transaccions i recuperació; només dades temporals."""
import copy
import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from src.persistencia import SnapshotStore, DataDirectoryLock, atomic_json


class Persistencia(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.store = SnapshotStore(self.directory)
        self.meta = {"active": "prova", "users": {"u1": {"name": "Anna"}}, "sessions": {"test-token": {"uid": "u1"}}}
        self.docs = {"game/state": {"hope": 6}}
        self.history = [{"id": "prova:1", "result": "win"}]

    def tearDown(self):
        self.temp.cleanup()

    def test_snapshot_conjunt_i_copies_json(self):
        self.store.commit(self.meta, self.docs, self.history)
        saved = SnapshotStore(self.directory).read()
        self.assertEqual(saved["meta"], self.meta)
        self.assertEqual(saved["docs"], self.docs)
        self.assertEqual(saved["history"], self.history)
        self.assertEqual(json.loads((self.directory / "partides/prova.json").read_text())["docs"], self.docs)
        self.assertEqual(json.loads((self.directory / "historial.json").read_text())["list"], self.history)

    def test_error_abans_del_commit_conserva_estat_anterior(self):
        self.store.commit(self.meta, self.docs, self.history)
        before = self.store.read()
        with patch.object(self.store, "_connect", side_effect=sqlite3.OperationalError("disk full")):
            with self.assertRaises(OSError):
                self.store.commit({**self.meta, "users": {}}, {"new": {}}, [])
        self.assertEqual(self.store.read(), before)

    def test_projeccio_fallida_es_recupera_en_reiniciar(self):
        self.store.commit(self.meta, self.docs, self.history)
        changed = {"game/state": {"hope": 3}}
        with patch("src.persistencia.atomic_json", side_effect=OSError("projection unavailable")):
            self.store.commit(self.meta, changed, [])
        self.assertIsNotNone(self.store.projection_error)
        self.assertEqual(self.store.read()["docs"], changed)
        fresh = SnapshotStore(self.directory)
        fresh.flush(force=True)
        self.assertEqual(json.loads((self.directory / "partides/prova.json").read_text())["docs"], changed)
        self.assertEqual(json.loads((self.directory / "historial.json").read_text())["list"], [])

    def test_projeccio_parcial_no_mescla_generacions(self):
        self.store.commit(self.meta, self.docs, self.history)
        calls = []
        def fail_second(path, obj):
            calls.append(path)
            if len(calls) == 2:
                raise OSError("power interrupted")
            atomic_json(path, obj)
        changed_meta = {**self.meta, "users": {"u1": {"name": "Anna nova"}}}
        with patch("src.persistencia.atomic_json", side_effect=fail_second):
            self.store.commit(changed_meta, {"game/state": {"hope": 2}}, [])
        SnapshotStore(self.directory).flush(force=True)
        self.assertEqual(json.loads((self.directory / "comunitat.json").read_text()), changed_meta)
        self.assertEqual(json.loads((self.directory / "partides/prova.json").read_text())["docs"]["game/state"]["hope"], 2)
        self.assertEqual(json.loads((self.directory / "historial.json").read_text())["list"], [])

    def test_no_deixa_una_partida_amb_projeccio_pendent(self):
        with patch("src.persistencia.atomic_json", side_effect=OSError("disk unavailable")):
            self.store.commit(self.meta, self.docs, self.history)
            with self.assertRaises(OSError):
                self.store.commit({**self.meta, "active": "altra"}, {}, [])
        self.assertEqual(self.store.read()["meta"]["active"], "prova")
        self.store.flush()

    def test_json_atomic_no_trunca_fitxer_i_neteja_temporal(self):
        path = self.directory / "example.json"
        atomic_json(path, {"previous": True})
        with patch("src.persistencia.os.replace", side_effect=OSError("write blocked")):
            with self.assertRaises(OSError):
                atomic_json(path, {"new": True})
        self.assertEqual(json.loads(path.read_text()), {"previous": True})
        self.assertFalse(list(self.directory.glob("*.tmp")))

    def test_sqlite_recupera_transaccio_interrompuda(self):
        self.store.commit(self.meta, self.docs, self.history)
        before = self.store.read()
        program = "import sqlite3,sys,os; d=sqlite3.connect(sys.argv[1]); d.execute('BEGIN IMMEDIATE'); d.execute(\"UPDATE snapshot SET body='incomplete' WHERE id=1\"); os._exit(7)"
        result = subprocess.run([sys.executable, "-c", program, str(self.store.path)])
        self.assertEqual(result.returncode, 7)
        self.assertEqual(SnapshotStore(self.directory).read(), before)

    def test_base_corrupta_no_es_recrea_ni_sobreescriu(self):
        self.store.path.write_bytes(b"damaged database")
        with self.assertRaises(OSError):
            self.store.commit(self.meta, self.docs, self.history)
        self.assertEqual(self.store.path.read_bytes(), b"damaged database")

    def test_integracio_migracio_historial_i_reinici(self):
        spec = importlib.util.spec_from_file_location("server_storage_test", ROOT / "comunitat.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.set_data_dir(self.directory)
        atomic_json(module.META, {"users": {"old": "Anna"}, "sessions": {}, "active": None})
        atomic_json(module.HIST, {"list": self.history})
        module.load()
        self.assertEqual(module.state["history"], self.history)
        self.assertIn("old", module.state["users"])
        original = copy.deepcopy(module.storage.read())
        module.META.write_text("corrupted mirror")
        module.HIST.write_text("corrupted mirror")
        module.load()
        self.assertEqual(module.state["history"], self.history)
        self.assertEqual(module.storage.read()["meta"]["users"], original["meta"]["users"])

    def test_copia_sqlite_es_coherent_i_no_la_pisa_una_base_corrupta(self):
        self.store.commit(self.meta, self.docs, self.history)
        self.store.backup()
        backup = self.directory / "copies/estat/comunitat.sqlite3"
        saved = backup.read_bytes()
        recovered = SnapshotStore(self.directory)
        recovered.path = backup
        self.assertEqual(recovered.read(), self.store.read())
        self.store.path.write_bytes(b"bad database")
        with self.assertRaises(OSError):
            self.store.backup()
        self.assertEqual(backup.read_bytes(), saved)

    def test_segona_instancia_no_pot_obrir_la_mateixa_carpeta(self):
        owner = DataDirectoryLock(self.directory)
        try:
            with self.assertRaises(OSError):
                DataDirectoryLock(self.directory)
        finally:
            owner.close()
        again = DataDirectoryLock(self.directory)
        again.close()

    def test_error_de_pin_restaura_credencial_i_sessio(self):
        spec = importlib.util.spec_from_file_location("server_pin_failure", ROOT / "comunitat.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.set_data_dir(self.directory)
        module.load()
        user = {"uid": "u1", "name": "Anna", "race": "home", "alias": "Inventada", "alias_gender": "female"}
        module.set_pin(user)
        module.state["users"]["u1"] = user
        module.state["sessions"]["previous"] = {"uid": "u1", "auth_version": 2, "dm": False}
        before = copy.deepcopy(module.state)
        handler = module.Handler.__new__(module.Handler)
        handler._json = lambda code, body: (code, body)
        with patch.object(module.storage, "commit", side_effect=OSError("disk full")):
            result = handler._players({"action": "pin", "uid": "u1"})
        self.assertEqual(result[0], 503)
        self.assertEqual(module.state["users"], before["users"])
        self.assertEqual(module.state["sessions"], before["sessions"])

    def test_partida_corrupta_es_conserva_sense_obrir_ne_una_buida(self):
        spec = importlib.util.spec_from_file_location("server_bad_campaign", ROOT / "comunitat.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.set_data_dir(self.directory)
        module.load()
        path = module.camp_file("damaged")
        path.write_text("incomplete campaign")
        with self.assertRaises(OSError):
            module.activate("damaged")
        self.assertEqual(path.read_text(), "incomplete campaign")
        self.assertIsNone(module.state["active"])

    def test_historial_antic_corrupt_no_es_perd(self):
        spec = importlib.util.spec_from_file_location("server_bad_legacy", ROOT / "comunitat.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.set_data_dir(self.directory)
        module.HIST.write_text("damaged legacy history")
        with self.assertRaises(OSError):
            module.load()
        self.assertEqual(module.HIST.read_text(), "damaged legacy history")
        self.assertIsNone(module.storage.read())


if __name__ == "__main__":
    unittest.main(verbosity=2)
