# SPDX-License-Identifier: GPL-3.0-or-later
"""Guardat transaccional de l'estat actiu i projeccions JSON compatibles.

SQLite és la font de l'últim estat confirmat. Els JSON són còpies compatibles:
si falla una projecció, l'estat confirmat continua en SQLite i es reintenta.
No es manté cap connexió oberta entre operacions ni es requerix cap servidor.
"""
import copy
import json
import os
import re
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path


def atomic_json(path, obj):
    """Substituïx un JSON complet, sense compartir temporals entre escriptures."""
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


class SnapshotStore:
    """Una transacció per a partida, identitats, sessions i historial."""
    def __init__(self, directory):
        self.directory = Path(directory)
        self.path = self.directory / "comunitat.sqlite3"
        self.projection_error = None

    def _connect(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        db = sqlite3.connect(str(self.path), timeout=5, isolation_level=None)
        try:
            if os.name == "posix":
                os.chmod(self.path, 0o600)
            db.execute("PRAGMA synchronous=FULL")
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise OSError("Unsupported save database version")
            db.execute("CREATE TABLE IF NOT EXISTS snapshot (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL, pending INTEGER NOT NULL)")
            if version == 0:
                db.execute("PRAGMA user_version=1")
            return db
        except Exception:
            db.close()
            raise

    def read(self):
        if not self.path.exists():
            return None
        try:
            with closing(self._connect()) as db:
                row = db.execute("SELECT body FROM snapshot WHERE id=1").fetchone()
            if not row:
                return None
            snapshot = json.loads(row[0])
            active = snapshot["meta"].get("active")
            if (snapshot.get("format") != 1 or not isinstance(snapshot["docs"], dict)
                    or not isinstance(snapshot["history"], list)
                    or (active is not None and (not isinstance(active, str) or not re.fullmatch(r"[a-z0-9-]{1,60}", active)))):
                raise ValueError("Invalid save snapshot")
            return snapshot
        except (sqlite3.Error, ValueError, KeyError, TypeError, AttributeError) as error:
            raise OSError("Cannot read save database: " + str(error)) from error

    def _targets(self, snapshot):
        targets = [(self.directory / "comunitat.json", snapshot["meta"]),
                   (self.directory / "historial.json", {"list": snapshot["history"]})]
        if snapshot["meta"].get("active"):
            targets.append((self.directory / "partides" / (snapshot["meta"]["active"] + ".json"), {"docs": snapshot["docs"]}))
        return targets

    def flush(self, force=False):
        """Recupera projeccions pendents. El caller bloqueja canvis concurrents."""
        snapshot = self.read()
        if snapshot is None:
            return
        try:
            with closing(self._connect()) as db:
                pending = db.execute("SELECT pending FROM snapshot WHERE id=1").fetchone()[0]
                if not force and not pending:
                    return
                for path, obj in self._targets(snapshot):
                    atomic_json(path, obj)
                db.execute("UPDATE snapshot SET pending=0 WHERE id=1")
            self.projection_error = None
        except sqlite3.Error as error:
            raise OSError("Cannot project save database: " + str(error)) from error

    def backup(self):
        """Còpia coherent de SQLite abans de la recuperació d'un nou inici."""
        if self.read() is None:
            return
        destination = self.directory / "copies" / "estat" / "comunitat.sqlite3"
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix="sqlite-backup-", dir=str(destination.parent))
        os.close(descriptor)
        try:
            with closing(self._connect()) as source, closing(sqlite3.connect(temporary)) as target:
                source.backup(target)
            with open(temporary, "r+b") as stream:
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        except sqlite3.Error as error:
            raise OSError("Cannot back up save database: " + str(error)) from error
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def commit(self, meta, docs, history):
        # Abans de deixar una partida, cal preservar-ne la còpia JSON completa.
        previous = self.read()
        if previous and previous["meta"].get("active") != meta.get("active"):
            self.flush()
        snapshot = {"format": 1, "meta": copy.deepcopy(meta), "docs": copy.deepcopy(docs), "history": copy.deepcopy(history)}
        try:
            body = json.dumps(snapshot, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as error:
            raise OSError("Invalid save data: " + str(error)) from error
        try:
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                try:
                    db.execute("INSERT OR REPLACE INTO snapshot(id, body, pending) VALUES(1, ?, 1)", (body,))
                    db.execute("COMMIT")
                except BaseException:
                    if db.in_transaction:
                        db.execute("ROLLBACK")
                    raise
        except sqlite3.Error as error:
            raise OSError("Cannot commit save database: " + str(error)) from error
        try:
            self.flush()
        except OSError as error:
            # Ja està confirmat i és recuperable: no falsegem una fallada de la jugada.
            self.projection_error = str(error)
        return snapshot


class DataDirectoryLock:
    """Impedix dos servidors escrivint la mateixa carpeta, també amb ports distints."""
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
            raise OSError("La carpeta de dades ja està oberta per un altre servidor.") from error

    def close(self):
        if self.stream.closed:
            return
        if os.name == "nt":
            import msvcrt
            self.stream.seek(0)
            msvcrt.locking(self.stream.fileno(), msvcrt.LK_UNLCK, 1)
        self.stream.close()
