#!/usr/bin/env python3
#
# La Comunitat — ajudant per a portar partides d'«El Señor de los Anillos:
# El Destino de la Comunidad».
# Copyright (C) 2026 Col·laboradors de La Comunitat
#
# Aquest programa és programari lliure: el podeu redistribuir i/o modificar
# segons els termes de la Llicència Pública General de GNU publicada per la
# Free Software Foundation, ja siga la versió 3 de la Llicència o (a la vostra
# elecció) qualsevol versió posterior.
#
# Aquest programa es distribueix amb l'esperança que siga útil, però SENSE CAP
# GARANTIA; ni tan sols la garantia implícita de COMERCIABILITAT o ADEQUACIÓ A
# UN PROPÒSIT PARTICULAR. Vegeu la Llicència Pública General de GNU per a més
# detalls: <https://www.gnu.org/licenses/>.
#
# Projecte de fans no oficial, sense relació amb Z-Man Games, Asmodee ni
# Middle-earth Enterprises.
"""
La Comunitat (versió 1.3) — servidor local per a portar partides de
«El Señor de los Anillos: El Destino de la Comunidad».

Tot va en aquest únic fitxer: el servidor i la pàgina web. Un ordinador
l'executa i la resta s'hi connecta des del navegador. És cooperatiu: tothom
pot fer canvis, no hi ha màster.

Ús (a Windows, canvia python3 per py, o fes doble clic a arrancar-windows.bat):
    python3 comunitat.py
    python3 comunitat.py --partida "Divendres"
    python3 comunitat.py --port 9001

Cada partida es guarda en un fitxer dins de la carpeta partides/.
Si poses una imatge mapa.jpg (o .png) al costat d'aquest fitxer, l'app la mostra al centre;
si no, mostra mapa-exemple.jpg.
"""
import argparse
import base64
import gzip
import json
import os
import queue
import re
import secrets
import socket
import sys
import threading
import time
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

VERSION = "1.3"
DIR = Path(__file__).resolve().parent
CAMP_DIR = DIR / "partides"
TRASH_DIR = CAMP_DIR / "esborrades"
META = DIR / "comunitat.json"     # sessions, player names, active campaign
OLD_DATA = DIR / "no-existeix.json"

lock = threading.RLock()
state = {
    "docs": {},        # active campaign: path -> dict
    "sessions": {},    # token -> {uid, dm}
    "users": {},       # uid -> name (shared by every campaign)
    "active": None,    # active campaign id
}
clients = []
dirty = threading.Event()
MASTER_PASSWORD = ""


# ---------------------------------------------------------------- storage
def write_json(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def camp_file(cid):
    return CAMP_DIR / f"{cid}.json"


def slugify(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40] or "partida"
    base, n = s, 2
    while camp_file(s).exists():
        s = f"{base}-{n}"
        n += 1
    return s


def camp_name(docs, cid):
    return ((docs.get("campaign/main") or {}).get("name") or "").strip() or cid


def list_campaigns():
    out = []
    for f in sorted(CAMP_DIR.glob("*.json")):
        cid = f.stem
        try:
            if cid == state["active"]:
                docs = state["docs"]
            else:
                docs = read_json(f).get("docs", {})
        except Exception:  # noqa: BLE001
            continue
        out.append({
            "id": cid,
            "name": camp_name(docs, cid),
            "updated": int(f.stat().st_mtime * 1000),
            "characters": sum(1 for p in docs if p.startswith("characters/")),
            "maps": sum(1 for p in docs if p.count("/") == 1 and p.startswith("maps/")),
            "notes": sum(1 for p in docs if p.startswith("notes/")),
            "active": cid == state["active"],
        })
    out.sort(key=lambda c: (not c["active"], -c["updated"]))
    return out


def save_now():
    with lock:
        meta = {"sessions": state["sessions"], "users": state["users"], "active": state["active"]}
        docs = {"docs": state["docs"]}
        cid = state["active"]
    write_json(META, meta)
    if cid:
        write_json(camp_file(cid), docs)


def saver():
    while True:
        dirty.wait()
        time.sleep(1.0)
        dirty.clear()
        try:
            save_now()
        except Exception as e:  # noqa: BLE001
            print(f"[!] No s'ha pogut guardar: {e}")


def activate(cid):
    """Load campaign `cid` as the active one (caller holds the lock and has saved the previous one)."""
    try:
        docs = read_json(camp_file(cid)).get("docs", {})
    except FileNotFoundError:
        docs = {}
    except Exception as e:  # noqa: BLE001
        bad = camp_file(cid).with_suffix(".json.danyat")
        camp_file(cid).replace(bad)
        print(f"[!] No s'ha pogut llegir {cid}.json ({e}). L'he mogut a {bad.name}.")
        docs = {}
    state["docs"] = docs
    state["active"] = cid


def new_campaign(name):
    cid = slugify(name)
    write_json(camp_file(cid), {"docs": {"campaign/main": {"name": name, "nextSession": ""}}})
    return cid


def load(wanted=None):
    CAMP_DIR.mkdir(exist_ok=True)
    if META.exists():
        try:
            meta = read_json(META)
            state["sessions"] = meta.get("sessions", {})
            state["users"] = meta.get("users", {})
            state["active"] = meta.get("active")
        except Exception as e:  # noqa: BLE001
            print(f"[!] No s'ha pogut llegir taula.json ({e}). Els jugadors hauran de tornar a entrar.")
    elif OLD_DATA.exists():
        # Migrate a version-2 partida.json into partides/ + taula.json
        try:
            old = read_json(OLD_DATA)
            docs = old.get("docs", {})
            state["sessions"] = old.get("sessions", {})
            for p in [p for p in docs if p.startswith("users/")]:
                state["users"][p.split("/")[1]] = (docs.pop(p) or {}).get("name", "")
            cid = slugify(camp_name(docs, "") or "la-meva-partida")
            write_json(camp_file(cid), {"docs": docs})
            state["active"] = cid
            OLD_DATA.replace(DIR / "partida.json.v2-importada")
            print(f"  He importat la teua partida anterior com a «{camp_name(docs, cid)}».")
        except Exception as e:  # noqa: BLE001
            print(f"[!] No s'ha pogut importar partida.json ({e}).")

    if wanted:
        state["active"] = None  # so list_campaigns reads every file from disk
        match = None
        for c in list_campaigns():
            if wanted in (c["id"], c["name"]) or slugify_plain(wanted) == c["id"]:
                match = c["id"]
                break
        state["active"] = match or new_campaign(wanted)
    if not state["active"] or not camp_file(state["active"]).exists():
        existing = sorted(CAMP_DIR.glob("*.json"), key=lambda f: -f.stat().st_mtime)
        state["active"] = existing[0].stem if existing else new_campaign("Primera partida")
    activate(state["active"])
    save_now()


def slugify_plain(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40]


# ---------------------------------------------------------------- helpers
def valid_path(p):
    if not isinstance(p, str) or not p or len(p) > 500:
        return False
    segs = p.split("/")
    if len(segs) % 2 or len(segs) > 16:
        return False
    ok = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.~:@+")
    return all(s and s not in (".", "..") and set(s) <= ok for s in segs)


def deep_merge(a, b):
    if not isinstance(a, dict) or not isinstance(b, dict):
        return b
    out = dict(a)
    for k, v in b.items():
        out[k] = deep_merge(a[k], v) if isinstance(v, dict) and isinstance(a.get(k), dict) else v
    return out


def seg(path):
    return path.split("/")


def get_doc(path):
    s = seg(path)
    if s[0] == "users" and len(s) == 2:
        n = state["users"].get(s[1])
        return {"name": n} if n is not None else None
    return state["docs"].get(path)


def visible_to(path, doc, sess):
    """Cooperative game: everyone sees everything."""
    return doc


def _unused_visible_to(path, doc, sess):
    if doc is None:
        return None
    if sess["dm"]:
        return doc
    s = seg(path)
    if s[0] == "dm":
        return None
    if s[0] == "maps":
        mp = state["docs"].get("maps/" + s[1])
        if not mp or not mp.get("visible"):
            return None
        if len(s) == 4 and doc.get("hidden"):
            return None
    return doc


def can_write(path, mode, new, sess):
    s = seg(path)
    if s[0] == "users":
        return len(s) == 2 and s[1] == sess["uid"] and mode != "delete"
    return s[0] in ("game", "map", "campaign")
    if sess["dm"]:
        return True
    docs = state["docs"]
    old = docs.get(path)
    if s[0] in ("dm", "campaign", "combat"):
        return False
    if s[0] == "rolls":
        return len(s) == 2 and s[1] == sess["uid"]
    if s[0] == "notes":
        return len(s) == 2
    if s[0] == "characters" and len(s) == 2:
        if old is not None and old.get("ownerId") != sess["uid"]:
            return False
        if mode != "delete":
            merged = deep_merge(old or {}, new) if mode == "update" else new
            if merged.get("ownerId") != sess["uid"]:
                return False
        return True
    if s[0] == "maps" and len(s) == 4 and s[2] == "tokens":
        mp = docs.get("maps/" + s[1])
        if not mp or not mp.get("visible"):
            return False

        def mine(tok):
            ch = docs.get("characters/" + str((tok or {}).get("charId")))
            return bool(ch) and ch.get("ownerId") == sess["uid"]

        if old is not None and not mine(old):
            return False
        if mode != "delete":
            merged = deep_merge(old or {}, new) if mode == "update" else new
            if not mine(merged) or merged.get("hidden"):
                return False
        return True
    return False


# ---------------------------------------------------------------- live updates
class Client:
    def __init__(self, sess):
        self.sess = sess
        self.q = queue.Queue(maxsize=2000)

    def send(self, kind, payload):
        try:
            self.q.put_nowait((kind, payload))
        except queue.Full:
            pass


def snapshot_for(sess):
    with lock:
        out = {}
        for p, d in state["docs"].items():
            v = visible_to(p, d, sess)
            if v is not None:
                out[p] = v
        for uid, name in state["users"].items():
            out["users/" + uid] = {"name": name}
        return out


def broadcast(changed):
    with lock:
        docs = state["docs"]
        extra = []
        for p in changed:
            s = seg(p)
            if s[0] == "maps" and len(s) == 2:  # map visibility changes what tokens players see
                pref = p + "/tokens/"
                extra += [k for k in docs if k.startswith(pref)]
        paths = list(dict.fromkeys(changed + extra))
        for c in list(clients):
            for p in paths:
                c.send("doc", {"path": p, "data": visible_to(p, get_doc(p), c.sess)})


def broadcast_switch():
    with lock:
        for c in list(clients):
            c.send("campaign", {"id": state["active"]})


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = "Comunitat/" + VERSION
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 2_000_000:
            raise ValueError("massa gran")
        return json.loads(self.rfile.read(n) or b"{}")

    def _session(self):
        tok = self.headers.get("X-Taula-Token") or ""
        if not tok:
            from urllib.parse import parse_qs, urlparse
            tok = (parse_qs(urlparse(self.path).query).get("t") or [""])[0]
        with lock:
            return state["sessions"].get(tok)

    def do_GET(self):
        route = self.path.split("?")[0]
        if route in ("/", "/index.html"):
            body = PAGE_BYTES
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("X-Taula-Version", VERSION)
            self.end_headers()
            self.wfile.write(body)
            return
        if route == "/mapa":
            for name, ctype in (("mapa.jpg", "image/jpeg"), ("mapa.jpeg", "image/jpeg"), ("mapa.png", "image/png"),
                                ("mapa.webp", "image/webp"), ("mapa-exemple.jpg", "image/jpeg")):
                f = DIR / name
                if f.exists():
                    body = f.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(len(body)))
                    self.send_header("Cache-Control", "no-cache")
                    self.end_headers()
                    self.wfile.write(body)
                    return
            return self._json(404, {"error": "No hi ha cap mapa.jpg"})
        if route == "/api/hello":
            return self._json(200, {"taula": 1, "version": VERSION})
        if route == "/api/campaigns":
            sess = self._session()
            if not sess:
                return self._json(401, {"error": "Sessió no vàlida"})
            with lock:
                return self._json(200, {"active": state["active"], "list": list_campaigns()})
        if route == "/api/snapshot":
            sess = self._session()
            if not sess:
                return self._json(401, {"error": "Sessió no vàlida"})
            with lock:
                return self._json(200, {"me": {"uid": sess["uid"], "dm": sess["dm"]},
                                        "campaign": state["active"], "docs": snapshot_for(sess)})
        if route == "/api/events":
            sess = self._session()
            if not sess:
                return self._json(401, {"error": "Sessió no vàlida"})
            return self._events(sess)
        self._json(404, {"error": "No trobat"})

    def _events(self, sess):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        # Padding pushes the stream past antivirus/proxy buffers that hold small responses back.
        try:
            self.wfile.write(b":" + b" " * 4096 + b"\nretry: 3000\n\n")
            self.wfile.flush()
        except OSError:
            return
        c = Client(sess)
        with lock:
            clients.append(c)
            first = {"me": {"uid": sess["uid"], "dm": sess["dm"]}, "campaign": state["active"],
                     "docs": snapshot_for(sess)}
        try:
            self._sse("snapshot", first)
            while True:
                try:
                    kind, payload = c.q.get(timeout=10)
                    self._sse(kind, payload)
                except queue.Empty:
                    self._sse("ping", {})
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
            pass
        finally:
            with lock:
                if c in clients:
                    clients.remove(c)

    def _sse(self, kind, payload):
        data = json.dumps(payload, ensure_ascii=False)
        self.wfile.write(f"event: {kind}\ndata: {data}\n\n".encode("utf-8"))
        self.wfile.flush()

    def do_POST(self):
        route = self.path.split("?")[0]
        try:
            body = self._body()
        except Exception:  # noqa: BLE001
            return self._json(400, {"error": "Petició mal formada"})
        if route == "/api/join":
            return self._join(body)
        if route == "/api/write":
            return self._write(body)
        if route == "/api/campaigns":
            return self._campaigns(body)
        self._json(404, {"error": "No trobat"})

    def _join(self, body):
        name = str(body.get("name") or "").strip()[:40]
        pw = str(body.get("password") or "")
        old_tok = str(body.get("token") or "")
        with lock:
            sess = state["sessions"].get(old_tok)
            if sess:
                tok = old_tok
            else:
                if not name:
                    return self._json(400, {"error": "Escriu el teu nom."})
                tok = secrets.token_urlsafe(24)
                sess = {"uid": "u" + secrets.token_hex(6), "dm": True}
                state["sessions"][tok] = sess
            if pw:
                if not secrets.compare_digest(pw, MASTER_PASSWORD):
                    if tok != old_tok:
                        state["sessions"].pop(tok, None)
                    return self._json(403, {"error": "La contrasenya del màster no és correcta."})
                sess["dm"] = True
            if name:
                state["users"][sess["uid"]] = name
            dirty.set()
        if name:
            broadcast(["users/" + sess["uid"]])
        return self._json(200, {"token": tok, "uid": sess["uid"], "dm": sess["dm"]})

    def _write(self, body):
        sess = self._session()
        if not sess:
            return self._json(401, {"error": "Sessió no vàlida. Torna a entrar."})
        path, mode, data = body.get("path"), body.get("mode"), body.get("data")
        if not valid_path(path) or mode not in ("set", "update", "delete"):
            return self._json(400, {"error": "Petició mal formada"})
        if mode != "delete" and not isinstance(data, dict):
            return self._json(400, {"error": "Petició mal formada"})
        if mode != "delete" and len(json.dumps(data)) > 256_000:
            return self._json(413, {"error": "Document massa gran"})
        with lock:
            if body.get("camp") and body.get("camp") != state["active"]:
                return self._json(409, {"error": "El màster ha canviat de partida."})
            if not can_write(path, mode, data, sess):
                return self._json(403, {"error": "No tens permís per a canviar això."})
            if seg(path)[0] == "users":
                merged = deep_merge(get_doc(path) or {}, data) if mode == "update" else data
                state["users"][sess["uid"]] = str(merged.get("name") or "")[:40]
            else:
                docs = state["docs"]
                if mode == "delete":
                    docs.pop(path, None)
                elif mode == "set":
                    docs[path] = data
                else:
                    docs[path] = deep_merge(docs.get(path) or {}, data)
            dirty.set()
        broadcast([path])
        return self._json(200, {"ok": True})

    def _campaigns(self, body):
        sess = self._session()
        if not sess:
            return self._json(401, {"error": "Sessió no vàlida. Torna a entrar."})
        if not sess["dm"]:
            return self._json(403, {"error": "No pots gestionar les partides."})
        action = body.get("action")
        name = str(body.get("name") or "").strip()[:80]
        cid = str(body.get("id") or "")
        if cid and not re.fullmatch(r"[a-z0-9-]{1,60}", cid):
            return self._json(400, {"error": "Partida desconeguda."})
        switched = False
        with lock:
            if action == "create":
                if not name:
                    return self._json(400, {"error": "Posa-li un nom a la partida."})
                save_now()
                activate(new_campaign(name))
                switched = True
            elif action == "switch":
                if not camp_file(cid).exists():
                    return self._json(404, {"error": "Aquesta partida ja no existeix."})
                if cid != state["active"]:
                    save_now()
                    activate(cid)
                    switched = True
            elif action == "duplicate":
                if not camp_file(cid).exists():
                    return self._json(404, {"error": "Aquesta partida ja no existeix."})
                save_now()
                docs = read_json(camp_file(cid)).get("docs", {})
                new_name = name or (camp_name(docs, cid) + " (còpia)")
                docs = dict(docs)
                docs["campaign/main"] = {**(docs.get("campaign/main") or {}), "name": new_name}
                new_id = slugify(new_name)
                write_json(camp_file(new_id), {"docs": docs})
            elif action == "delete":
                if cid == state["active"]:
                    return self._json(400, {"error": "No pots esborrar la partida oberta. Obri'n una altra primer."})
                if not camp_file(cid).exists():
                    return self._json(404, {"error": "Aquesta partida ja no existeix."})
                TRASH_DIR.mkdir(exist_ok=True)
                camp_file(cid).replace(TRASH_DIR / f"{cid}-{time.strftime('%Y%m%d-%H%M%S')}.json")
            else:
                return self._json(400, {"error": "Acció desconeguda."})
            dirty.set()
            result = {"active": state["active"], "list": list_campaigns()}
        if switched:
            save_now()
            broadcast_switch()
        return self._json(200, result)


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


def lan_addresses():
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    return sorted(ip for ip in ips if not ip.startswith("127."))


def main():
    global MASTER_PASSWORD
    for stream in (sys.stdout, sys.stderr):  # Windows consoles may not speak UTF-8
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    ap = argparse.ArgumentParser(description="Servidor local de La Comunitat")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--master-password", default=os.environ.get("TAULA_MASTER_PASSWORD", ""))
    ap.add_argument("--partida", default="", help="nom de la partida que s'obri en arrancar (la crea si no existeix)")
    a = ap.parse_args()
    MASTER_PASSWORD = secrets.token_hex(8)  # cooperative game: nobody uses it
    try:
        srv = Server(("0.0.0.0", a.port), Handler)
    except OSError:
        sys.exit(
            f"\n  El port {a.port} ja està en ús: hi ha un altre programa (potser un servidor antic) escoltant-hi.\n"
            f"  Per a veure quin és:   ss -ltnp | grep {a.port}\n"
            f"  O arranca en un altre port:   python3 comunitat.py --port 9001\n")
    load(a.partida.strip() or None)
    threading.Thread(target=saver, daemon=True).start()
    print(f"\n  La Comunitat (versió {VERSION}) està en marxa.\n")
    print(f"  En aquest ordinador:   http://localhost:{a.port}")
    for ip in lan_addresses():
        print(f"  Des de la xarxa:       http://{ip}:{a.port}")
    print()
    print(f"  Partida oberta:         {camp_name(state['docs'], state['active'])}")
    print(f"  Partides guardades a:   {CAMP_DIR}")
    print("\n  Prem Ctrl+C per a aturar-lo.\n")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        save_now()
        print("\n  Partida guardada. Fins la pròxima!\n")


# ---------------------------------------------------------------- web page (gzip + base64)
PAGE_BYTES = gzip.decompress(base64.b64decode("""
__PAGE__
"""))

if __name__ == "__main__":
    main()
