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
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
"""))

if __name__ == "__main__":
    main()
