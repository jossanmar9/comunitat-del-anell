# SPDX-License-Identifier: GPL-3.0-or-later
"""Escriptura segura dels fitxers de dades, bloqueig de la carpeta i migració de la v2.
Incrustat per build.py en el programa (les proves també l'importen directament).
"""
import json
import os
import re
import tempfile
from pathlib import Path


def atomic_json(path, obj):
    """Substitueix un JSON complet: s'escriu a un temporal, es força al disc i es reanomena."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(obj, stream, ensure_ascii=False, indent=1, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
        if os.name == "posix":
            directory = os.open(str(path.parent), os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


class DataDirectoryLock:
    """Impedeix que dos programes escriguen alhora la mateixa carpeta de dades."""

    def __init__(self, directory):
        Path(directory).mkdir(parents=True, exist_ok=True)
        self.stream = open(Path(directory) / "comunitat.lock", "a+b")
        try:
            if os.name == "nt":
                import msvcrt
                self.stream.seek(0)
                if not self.stream.read(1):
                    self.stream.write(b"0")
                    self.stream.flush()
                self.stream.seek(0)
                msvcrt.locking(self.stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            self.stream.close()
            raise OSError("La carpeta de dades ja està oberta per un altre programa.") from error

    def close(self):
        if self.stream.closed:
            return
        if os.name == "nt":
            import msvcrt
            self.stream.seek(0)
            msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
        self.stream.close()


def migra_v2(directory):
    """Les versions 2.7 guardaven l'últim estat en comunitat.sqlite3 i en feien còpies JSON. Si la
    còpia JSON es va quedar a mitjan fer, s'escriu ara; després la base de dades es guarda a
    copies/v2/ i ja no es fa servir. També es lleva de comunitat.json el que era de la sala (jugadors,
    PIN i sessions)."""
    directory = Path(directory)
    db_path = directory / "comunitat.sqlite3"
    if db_path.exists():
        import sqlite3
        from contextlib import closing
        try:
            with closing(sqlite3.connect(str(db_path), timeout=5)) as db:
                row = db.execute("SELECT body, pending FROM snapshot WHERE id=1").fetchone()
            if row and row[1]:
                snapshot = json.loads(row[0])
                active = snapshot["meta"].get("active")
                atomic_json(directory / "historial.json", {"list": snapshot["history"]})
                if isinstance(active, str) and re.fullmatch(r"[a-z0-9-]{1,60}", active):
                    atomic_json(directory / "partides" / (active + ".json"), {"docs": snapshot["docs"]})
                    atomic_json(directory / "comunitat.json", {"versio": 3, "active": active})
        except Exception as error:  # noqa: BLE001
            print(f"[!] No s'ha pogut llegir comunitat.sqlite3 ({error}). Es fan servir els fitxers JSON.")
        destination = directory / "copies" / "v2"
        destination.mkdir(parents=True, exist_ok=True)
        for f in directory.glob("comunitat.sqlite3*"):
            try:
                f.replace(destination / f.name)
            except OSError:
                pass
    meta = directory / "comunitat.json"
    if meta.exists():
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
            if isinstance(data, dict) and set(data) - {"versio", "active"}:
                active = data.get("active")
                atomic_json(meta, {"versio": 3, "active": active if isinstance(active, str) else None})
        except (OSError, ValueError):
            pass
