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
La Comunitat (versió 2.0) — servidor local per a portar partides de
«El Señor de los Anillos: El Destino de la Comunidad».

Tot va en aquest únic fitxer: el servidor, la pàgina web i els mapes d'exemple.
Un ordinador l'executa i la resta s'hi connecta des del navegador. És cooperatiu:
tothom pot fer canvis, no hi ha màster.

Ús (a Windows, canvia python3 per py, o fes doble clic a arrancar-windows.bat):
    python3 comunitat.py
    python3 comunitat.py --partida "Divendres" --port 9001
    python3 comunitat.py --sense-finestra       (només la terminal)
    python3 comunitat.py --dades CARPETA         (on es guarden les partides)

En arrancar obri una finestreta (i la terminal) amb l'adreça i un codi QR per a entrar
des del mòbil.
Les dades van al costat del programa, o a la carpeta de l'usuari si el programa està
instal·lat: cada partida a partides/<nom>.json, les partides acabades a historial.json.
Si poses una imatge mapa.jpg (o .png) a la carpeta de dades, l'app la mostra al centre.
També pots posar mapa-val.jpg i mapa-es.jpg, un per idioma. Si no n'hi ha cap, mostra
el mapa d'exemple de l'idioma de qui mira.
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
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

VERSION = "2.0"
FROZEN = getattr(sys, "frozen", False)          # executable de Windows fet amb PyInstaller
DIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
INSTALLAT = (DIR / "installat").exists()       # el posen l'instal·lador de Windows i el paquet .deb
NOM = "La Comunitat"


def user_data_dir():
    """La carpeta de dades de l'usuari, per a quan el programa està instal·lat."""
    if os.name == "nt":
        return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "LaComunitat"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "La Comunitat"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "comunitat-del-anell"


def set_data_dir(path):
    global DATA_DIR, CAMP_DIR, TRASH_DIR, META, HIST
    DATA_DIR = Path(path).expanduser().resolve()
    CAMP_DIR = DATA_DIR / "partides"
    TRASH_DIR = CAMP_DIR / "esborrades"
    META = DATA_DIR / "comunitat.json"     # sessions, noms dels jugadors i partida oberta
    HIST = DATA_DIR / "historial.json"     # partides acabades


set_data_dir(user_data_dir() if INSTALLAT else DIR)

lock = threading.RLock()
state = {
    "docs": {},        # partida oberta: ruta -> dict
    "sessions": {},    # token -> {uid, dm}
    "users": {},       # uid -> nom (comú a totes les partides)
    "active": None,    # id de la partida oberta
    "history": [],     # partides acabades
    "port": 8766,
}
clients = []
dirty = threading.Event()


# ---------------------------------------------------------------- emmagatzematge
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


def slugify_plain(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")[:40]


def slugify(name):
    s = slugify_plain(name) or "partida"
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
            docs = state["docs"] if cid == state["active"] else read_json(f).get("docs", {})
        except Exception:  # noqa: BLE001
            continue
        out.append({
            "id": cid,
            "name": camp_name(docs, cid),
            "updated": int(f.stat().st_mtime * 1000),
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
    """Carrega la partida `cid` com a oberta (qui crida té el lock i ja ha guardat l'anterior)."""
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
    write_json(camp_file(cid), {"docs": {"campaign/main": {"name": name}}})
    return cid


def load(wanted=None):
    CAMP_DIR.mkdir(parents=True, exist_ok=True)
    if META.exists():
        try:
            meta = read_json(META)
            state["sessions"] = meta.get("sessions", {})
            state["users"] = meta.get("users", {})
            state["active"] = meta.get("active")
        except Exception as e:  # noqa: BLE001
            print(f"[!] No s'ha pogut llegir comunitat.json ({e}). Els jugadors hauran de tornar a entrar.")
    if wanted:
        state["active"] = None  # perquè list_campaigns llija tots els fitxers del disc
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


# ---------------------------------------------------------------- historial
def load_history():
    if HIST.exists():
        try:
            state["history"] = read_json(HIST).get("list", [])
        except Exception as e:  # noqa: BLE001
            print(f"[!] No s'ha pogut llegir historial.json ({e}).")


def save_history():
    write_json(HIST, {"list": state["history"]})


def track_result(g):
    """Apunta o desapunta una partida acabada quan canvia game/state (qui crida té el lock)."""
    if not isinstance(g, dict) or not g.get("created"):
        return False
    hid = f"{state['active']}:{g['created']}"
    hist = state["history"]
    old = next((h for h in hist if h["id"] == hid), None)
    res = g.get("result")
    if res not in ("win", "lose"):
        if old:
            hist.remove(old)
            return True
        return False
    if old and old["result"] == res:
        return False
    objs = [o for o in g.get("objectives", []) if isinstance(o, dict)]
    rec = {
        "id": hid,
        "camp": camp_name(state["docs"], state["active"]),
        "result": res,
        "level": g.get("level"),
        "players": [str((p or {}).get("name") or "") for p in g.get("players", [])],
        "chars": [str((c or {}).get("id") or "") for c in g.get("chars", [])],
        "objectives": [str(o.get("name") or "") for o in objs if not o.get("ring")],
        "done": sum(1 for o in objs if o.get("done")),
        "rounds": g.get("round"),
        "hope": g.get("hope"),
        "created": g.get("created"),
        "ended": g.get("ended") or int(time.time() * 1000),
    }
    if old:
        hist[hist.index(old)] = rec
    else:
        hist.append(rec)
    return True


# ---------------------------------------------------------------- documents
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


def can_write(path, mode, sess):
    """Joc cooperatiu: tothom pot canviar la partida; cadascú només el seu nom."""
    s = seg(path)
    if s[0] == "users":
        return len(s) == 2 and s[1] == sess["uid"] and mode != "delete"
    return s[0] in ("game", "map", "campaign")


# ---------------------------------------------------------------- actualitzacions en directe
class Client:
    def __init__(self, sess):
        self.sess = sess
        self.q = queue.Queue(maxsize=2000)

    def send(self, kind, payload):
        try:
            self.q.put_nowait((kind, payload))
        except queue.Full:
            pass


def snapshot():
    with lock:
        out = dict(state["docs"])
        for uid, name in state["users"].items():
            out["users/" + uid] = {"name": name}
        return out


def broadcast(paths):
    with lock:
        for c in list(clients):
            for p in paths:
                c.send("doc", {"path": p, "data": get_doc(p)})


def broadcast_event(kind, payload):
    with lock:
        for c in list(clients):
            c.send(kind, payload)


# ---------------------------------------------------------------- mapa
MAP_EXTS = (("jpg", "image/jpeg"), ("jpeg", "image/jpeg"), ("png", "image/png"), ("webp", "image/webp"))


def map_image(lang):
    """El mapa propi de la carpeta de dades (per idioma o general) o, si no n'hi ha, el d'exemple."""
    for d in dict.fromkeys((DATA_DIR, DIR)):
        for name in (f"mapa-{lang}", "mapa"):
            for ext, ctype in MAP_EXTS:
                f = d / f"{name}.{ext}"
                if f.is_file():
                    return f.read_bytes(), ctype
    return MAPES[lang], "image/jpeg"


# ---------------------------------------------------------------- QR (sense dependències)
__QR__


__FINESTRA__


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


def lan_urls():
    return [f"http://{ip}:{state['port']}" for ip in lan_addresses()]


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = "Comunitat/" + VERSION
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8", {"Cache-Control": "no-store"})

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 2_000_000:
            raise ValueError("massa gran")
        return json.loads(self.rfile.read(n) or b"{}")

    def _query(self):
        return parse_qs(urlparse(self.path).query)

    def _session(self):
        tok = self.headers.get("X-Taula-Token") or (self._query().get("t") or [""])[0]
        with lock:
            return state["sessions"].get(tok)

    # -- GET
    def do_GET(self):
        route = self.path.split("?")[0]
        if route in ("/", "/index.html"):
            return self._send(200, PAGE_BYTES, "text/html; charset=utf-8",
                              {"Cache-Control": "no-store", "X-Taula-Version": VERSION})
        if route == "/mapa":
            lang = "es" if (self._query().get("lang") or ["val"])[0] == "es" else "val"
            body, ctype = map_image(lang)
            return self._send(200, body, ctype, {"Cache-Control": "no-cache"})
        if route == "/api/hello":
            return self._json(200, {"taula": 1, "version": VERSION})
        if route == "/api/invite":
            urls = lan_urls() or [f"http://localhost:{state['port']}"]
            return self._json(200, {"list": [{"url": u, "svg": qr_svg(u)} for u in urls]})
        sess = self._session()
        if route in ("/api/history", "/api/campaigns", "/api/snapshot", "/api/events") and not sess:
            return self._json(401, {"error": "Sessió no vàlida. Torna a entrar."})
        if route == "/api/history":
            with lock:
                return self._json(200, {"list": list(reversed(state["history"]))})
        if route == "/api/campaigns":
            with lock:
                return self._json(200, {"active": state["active"], "list": list_campaigns()})
        if route == "/api/snapshot":
            with lock:
                return self._json(200, {"me": {"uid": sess["uid"], "dm": True},
                                        "campaign": state["active"], "docs": snapshot()})
        if route == "/api/events":
            return self._events(sess)
        self._json(404, {"error": "No trobat"})

    def _events(self, sess):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        # El farciment fa passar el flux pels antivirus i intermediaris que retenen les respostes curtes.
        try:
            self.wfile.write(b":" + b" " * 4096 + b"\nretry: 3000\n\n")
            self.wfile.flush()
        except OSError:
            return
        c = Client(sess)
        with lock:
            clients.append(c)
            first = {"me": {"uid": sess["uid"], "dm": True}, "campaign": state["active"], "docs": snapshot()}
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

    # -- POST
    def do_POST(self):
        route = self.path.split("?")[0]
        try:
            body = self._body()
        except Exception:  # noqa: BLE001
            return self._json(400, {"error": "Petició mal formada"})
        if route == "/api/join":
            return self._join(body)
        sess = self._session()
        if not sess:
            return self._json(401, {"error": "Sessió no vàlida. Torna a entrar."})
        if route == "/api/write":
            return self._write(body, sess)
        if route == "/api/campaigns":
            return self._campaigns(body)
        if route == "/api/history":
            return self._history(body)
        self._json(404, {"error": "No trobat"})

    def _join(self, body):
        name = str(body.get("name") or "").strip()[:40]
        old_tok = str(body.get("token") or "")
        with lock:
            sess = state["sessions"].get(old_tok)
            if sess:
                tok = old_tok
            else:
                if not name:
                    return self._json(400, {"error": "Escriu el teu nom."})
                tok = secrets.token_urlsafe(24)
                sess = {"uid": "u" + secrets.token_hex(6)}
                state["sessions"][tok] = sess
            if name:
                state["users"][sess["uid"]] = name
            dirty.set()
        if name:
            broadcast(["users/" + sess["uid"]])
        return self._json(200, {"token": tok, "uid": sess["uid"], "dm": True})

    def _write(self, body, sess):
        path, mode, data = body.get("path"), body.get("mode"), body.get("data")
        if not valid_path(path) or mode not in ("set", "update", "delete"):
            return self._json(400, {"error": "Petició mal formada"})
        if mode != "delete" and not isinstance(data, dict):
            return self._json(400, {"error": "Petició mal formada"})
        if mode != "delete" and len(json.dumps(data)) > 256_000:
            return self._json(413, {"error": "Document massa gran"})
        with lock:
            if body.get("camp") and body.get("camp") != state["active"]:
                return self._json(409, {"error": "S'ha obert una altra partida."})
            if not can_write(path, mode, sess):
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
                if path == "game/state" and track_result(docs.get(path)):
                    save_history()
            dirty.set()
        broadcast([path])
        return self._json(200, {"ok": True})

    def _history(self, body):
        hid = str(body.get("id") or "")
        with lock:
            if body.get("action") == "delete":
                state["history"] = [h for h in state["history"] if h["id"] != hid]
                save_history()
            return self._json(200, {"list": list(reversed(state["history"]))})

    def _campaigns(self, body):
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
                write_json(camp_file(slugify(new_name)), {"docs": docs})
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
            broadcast_event("campaign", {"id": state["active"]})
        return self._json(200, result)


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


def main():
    for name in ("stdout", "stderr"):  # l'executable de Windows no té terminal
        if getattr(sys, name) is None:
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))
    for stream in (sys.stdout, sys.stderr):  # les consoles de Windows potser no parlen UTF-8
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    if os.name == "nt":
        os.system("")  # activa els colors ANSI de la consola de Windows (per al QR)
    ap = argparse.ArgumentParser(description="Servidor local de La Comunitat")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--partida", default="", help="nom de la partida que s'obri en arrancar (la crea si no existeix)")
    ap.add_argument("--dades", default=os.environ.get("COMUNITAT_DADES", ""),
                    help="carpeta on es guarden les partides (per defecte, al costat del programa, "
                         "o a la carpeta de l'usuari si està instal·lat)")
    ap.add_argument("--sense-finestra", action="store_true", help="no obri la finestra: només la terminal")
    ap.add_argument("--sense-navegador", action="store_true", help="no obri el navegador en arrancar")
    ap.add_argument("--sense-qr", action="store_true", help="no mostra el codi QR a la terminal")
    ap.add_argument("--idioma", choices=("ca", "es"), help="idioma de la finestra (per defecte, el del sistema)")
    a = ap.parse_args()
    if a.dades.strip():
        set_data_dir(a.dades.strip())
    amb_finestra = not a.sense_finestra and hi_ha_finestra()
    idioma = a.idioma or idioma_sistema()
    state["port"] = a.port
    try:
        srv = Server(("0.0.0.0", a.port), Handler)
    except OSError:
        print(f"\n  El port {a.port} ja està en ús: hi ha un altre programa (potser La Comunitat ja oberta) escoltant-hi.\n"
              f"  Tanca'l, o arranca en un altre port:   python3 comunitat.py --port 9001\n")
        if amb_finestra:
            T = FINESTRA_TEXTOS[idioma]
            avis_finestra(T["port_t"], T["port_q"].format(p=a.port))
        sys.exit(1)
    load(a.partida.strip() or None)
    load_history()
    threading.Thread(target=saver, daemon=True).start()
    try:  # en apagar l'ordinador o tancar la sessió (Linux), es guarda igual que amb Ctrl+C
        import signal
        signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    except Exception:  # noqa: BLE001
        pass
    print(f"\n  La Comunitat (versió {VERSION}) està en marxa.\n")
    print(f"  En aquest ordinador:   http://localhost:{a.port}")
    urls = lan_urls()
    for u in urls:
        print(f"  Des de la xarxa:       {u}")
    if urls and not a.sense_qr and not amb_finestra:
        print("\n  Escaneja aquest codi amb el mòbil per a entrar:\n")
        try:
            print(qr_terminal(urls[0]))
        except Exception:  # noqa: BLE001
            pass
    print()
    print(f"  Partida oberta:         {camp_name(state['docs'], state['active'])}")
    print(f"  Dades guardades a:      {DATA_DIR}")
    try:
        if amb_finestra:
            print("\n  Tanca la finestra de La Comunitat per a aturar-la.\n")
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            finestra(a.port, idioma, obrir_navegador=not a.sense_navegador)
            srv.shutdown()
        else:
            print("\n  Prem Ctrl+C per a aturar-la" + (" o tanca aquesta finestra" if os.name == "nt" else "") + ".\n")
            if FROZEN and not a.sense_navegador:
                threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{a.port}")).start()
            srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        save_now()
        print("\n  Partida guardada. Fins la pròxima!\n")


# ---------------------------------------------------------------- pàgina web i mapes d'exemple (base64)
PAGE_BYTES = gzip.decompress(base64.b64decode("""
__PAGE__
"""))
MAPES = {
    "val": base64.b64decode("""
__MAPA_VAL__
"""),
    "es": base64.b64decode("""
__MAPA_ES__
"""),
}
ICONA_PNG = "".join("""
__ICONA__
""".split())

if __name__ == "__main__":
    main()
