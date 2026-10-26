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
La Comunitat (versió 2.4.2) — servidor local per a portar partides de
«El Señor de los Anillos: El Destino de la Comunidad».

Tot va en aquest únic fitxer: el servidor, la pàgina web i els mapes d'exemple.
Un ordinador l'executa i la resta s'hi connecta des del navegador. És cooperatiu:
tothom pot fer canvis, no hi ha màster.

Ús (a Windows, canvia python3 per py, o fes doble clic a arrancar-windows.bat):
    python3 comunitat.py
    python3 comunitat.py --partida "Divendres" --port 9001
    python3 comunitat.py --navegador            (l'app al navegador, amb la finestreta del QR)
    python3 comunitat.py --sense-finestra       (només el terminal)
    python3 comunitat.py --dades CARPETA         (on es guarden les partides)

En arrancar obri l'app en una finestra pròpia (a Windows amb WebView2, a Linux amb WebKitGTK).
Si no es pot, obri una finestreta amb l'adreça i un codi QR, i l'app al navegador.
Les dades van al costat del programa, o a la carpeta de l'usuari si el programa està
instal·lat: cada partida a partides/<nom>.json, les partides acabades a historial.json i
còpies de seguretat automàtiques a copies/<nom>/.
Si poses una imatge mapa.jpg (o .png) a la carpeta de dades, l'app la mostra al centre.
També pots posar mapa-val.jpg i mapa-es.jpg, un per idioma. Si no n'hi ha cap, mostra
el mapa d'exemple de l'idioma de qui mira.
"""
import argparse
import base64
import copy
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

VERSION = "2.4.2"
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

BACKUP_KEEP = 15            # còpies que es guarden de cada partida
BACKUP_EVERY = 30 * 60      # mentre es juga, una còpia cada mitja hora (si hi ha hagut canvis)
BACKUP_RE = re.compile(r"\d{8}-\d{6}(?:-\d+)?-[a-z]+")
MAX_IMPORT = 5 * 1024 * 1024

lock = threading.RLock()
state = {
    "epoch": secrets.token_hex(12),
    "revision": 0,  # epoch distingeix les revisions després de reiniciar
    "docs": {},        # partida oberta: ruta -> dict
    "sessions": {},    # token -> {uid, dm}
    "users": {},       # uid -> nom (comú a totes les partides)
    "active": None,    # id de la partida oberta
    "history": [],     # partides acabades
    "port": 8766,
    "last_backup": 0,  # quan s'ha fet l'última còpia automàtica de la partida oberta
}
clients = []
completed_requests = {}
dirty = threading.Event()


# ---------------------------------------------------------------- emmagatzematge
def write_json(path, obj):
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.flush()
        os.fsync(f.fileno())
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


def list_trash():
    out = []
    for f in sorted(TRASH_DIR.glob("*.json"), reverse=True):
        try:
            out.append({"id": f.stem, "name": camp_name(read_json(f).get("docs", {}), f.stem)})
        except (OSError, ValueError, AttributeError):
            continue
    return out


def save_now():
    with lock:
        meta = copy.deepcopy({"sessions": state["sessions"], "users": state["users"], "active": state["active"]})
        docs = {"docs": copy.deepcopy(state["docs"])}
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
            with lock:
                save_history()
            if time.time() - state["last_backup"] > BACKUP_EVERY:
                with lock:
                    cid, docs = state["active"], copy.deepcopy(state["docs"])
                    state["last_backup"] = time.time()
                make_backup(cid, docs, "partida")
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
    state["revision"] += 1
    state["active"] = cid
    state["last_backup"] = time.time()
    try:
        make_backup(cid, docs, "obrir")
    except OSError as e:
        print(f"[!] No s'ha pogut fer la còpia de seguretat de {cid}: {e}")


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


# ---------------------------------------------------------------- còpies de seguretat
def backup_dir(cid):
    return DATA_DIR / "copies" / cid


def make_backup(cid, docs, reason):
    """Guarda una còpia de la partida a copies/<partida>/ i esborra les més antigues."""
    if not cid or not docs or len(docs) <= 1:     # una partida acabada de crear encara no té res a guardar
        return None
    d = backup_dir(cid)
    d.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    name, n = f"{stamp}-{reason}", 2
    while (d / f"{name}.json").exists():
        name, n = f"{stamp}-{n}-{reason}", n + 1
    write_json(d / f"{name}.json", {"docs": docs})
    for old in sorted(d.glob("*.json"), key=lambda f: (f.stat().st_mtime_ns, f.name))[:-BACKUP_KEEP]:
        try:
            old.unlink()
        except OSError:
            pass
    return name


def list_backups(cid):
    d = backup_dir(cid)
    if not d.exists():
        return []
    out = []
    for f in sorted(d.glob("*.json"), key=lambda f: (f.stat().st_mtime_ns, f.name), reverse=True):
        if not BACKUP_RE.fullmatch(f.stem):
            continue
        st_ = f.stat()
        out.append({"id": f.stem, "ts": int(st_.st_mtime * 1000), "reason": f.stem.rsplit("-", 1)[1]})
    return out


def campaign_docs(cid):
    """Els documents d'una partida (la oberta, des de la memòria)."""
    if cid == state["active"]:
        return copy.deepcopy(state["docs"])
    return read_json(camp_file(cid)).get("docs", {})


# ---------------------------------------------------------------- exportar i importar
class ImportError_(Exception):
    pass


NO_ES_PARTIDA = "El fitxer no és una partida de La Comunitat."


def check_docs(docs):
    if not isinstance(docs, dict) or len(docs) > 5000:
        raise ImportError_(NO_ES_PARTIDA)
    for k, v in docs.items():
        if not valid_path(k) or not isinstance(v, dict) or seg(k)[0] not in ("game", "map", "campaign"):
            raise ImportError_(NO_ES_PARTIDA)
    name = docs.get("campaign/main", {}).get("name", "")
    if not isinstance(name, str) or len(name) > 80:
        raise ImportError_(NO_ES_PARTIDA)
    if "game/state" in docs:
        check_game(docs["game/state"])
    log = docs.get("game/log", {}).get("list", [])
    undo = docs.get("game/undo", {}).get("stack", [])
    if not isinstance(log, list) or len(log) > 600 or any(not isinstance(e, dict) for e in log):
        raise ImportError_(NO_ES_PARTIDA)
    if not isinstance(undo, list) or len(undo) > 30:
        raise ImportError_(NO_ES_PARTIDA)
    for item in undo:
        if not isinstance(item, dict) or not isinstance(item.get("state"), dict):
            raise ImportError_(NO_ES_PARTIDA)
        check_game(item["state"])
    return docs


def check_game(g):
    """Valida també els camps necessaris per a representar una partida."""
    if g.get("v") != 2:
        raise ImportError_(NO_ES_PARTIDA)
    for key, low, high in (("hope", 0, 8), ("hopeMax", 1, 8), ("round", 1, 100000),
                           ("deck", 0, 1000), ("threatIdx", 0, 100), ("created", 1, 10**16)):
        value = g.get(key)
        if type(value) is not int or not low <= value <= high:
            raise ImportError_(NO_ES_PARTIDA)
    for key in ("players", "chars", "objectives"):
        value = g.get(key)
        if not isinstance(value, list) or not 1 <= len(value) <= 30 or any(not isinstance(e, dict) for e in value):
            raise ImportError_(NO_ES_PARTIDA)
    if any(not isinstance(p.get("name"), str) for p in g["players"]):
        raise ImportError_(NO_ES_PARTIDA)
    if any(not isinstance(c.get("id"), str) for c in g["chars"]):
        raise ImportError_(NO_ES_PARTIDA)
    if any(not isinstance(o.get("name"), str) or type(o.get("done")) is not bool for o in g["objectives"]):
        raise ImportError_(NO_ES_PARTIDA)
    threat = g.get("threat")
    if (not isinstance(threat, list) or not threat or len(threat) > 100
            or any(type(n) is not int or not 0 <= n <= 100 for n in threat)
            or g["threatIdx"] >= len(threat) or g["hope"] > g["hopeMax"]):
        raise ImportError_(NO_ES_PARTIDA)
    if not isinstance(g.get("setup"), list) or any(type(v) is not bool for v in g["setup"]):
        raise ImportError_(NO_ES_PARTIDA)
    for key in ("turn", "skies", "calc"):
        if not isinstance(g.get(key), dict):
            raise ImportError_(NO_ES_PARTIDA)
    turn = g["turn"]
    for key, limit in (("p", len(g["players"])-1), ("step", 20), ("shadow", 100)):
        if type(turn.get(key)) is not int or not 0 <= turn[key] <= limit:
            raise ImportError_(NO_ES_PARTIDA)
    if not isinstance(turn.get("a"), list) or len(turn["a"]) != 2 or any(type(n) is not int or n < 0 for n in turn["a"]):
        raise ImportError_(NO_ES_PARTIDA)
    for key in ("total", "drawn"):
        if type(g["skies"].get(key)) is not int or not 0 <= g["skies"][key] <= 100:
            raise ImportError_(NO_ES_PARTIDA)
    if g.get("result") not in (None, "win", "lose"):
        raise ImportError_(NO_ES_PARTIDA)
    if g.get("level") not in ("intro", "estandard", "heroica", "epica", "llegendaria") or type(g.get("solo")) is not bool:
        raise ImportError_(NO_ES_PARTIDA)
    calc = g["calc"]
    for key in ("naz", "troops", "bFr", "bSh"):
        if type(calc.get(key)) is not int or not 0 <= calc[key] <= 100000:
            raise ImportError_(NO_ES_PARTIDA)
    for key in ("ring", "haven", "mordor", "bNaz", "bHaven"):
        if type(calc.get(key)) is not bool:
            raise ImportError_(NO_ES_PARTIDA)
    if calc.get("bKind") not in ("attack", "shadow"):
        raise ImportError_(NO_ES_PARTIDA)


def export_json(cid):
    docs = campaign_docs(cid)
    name = camp_name(docs, cid)
    info = {"format": "comunitat-del-anell", "versio": 1, "programa": VERSION, "nom": name,
            "exportada": time.strftime("%Y-%m-%d %H:%M"), "docs": docs}
    return name, json.dumps(info, ensure_ascii=False, indent=1).encode("utf-8")


def import_campaign(data):
    """Crea una partida nova a partir d'un fitxer exportat (o d'un .json de partides/ o de copies/). Torna l'id."""
    try:
        info = json.loads(data.decode("utf-8-sig"))
    except Exception as e:  # noqa: BLE001
        raise ImportError_(NO_ES_PARTIDA) from e
    if not isinstance(info, dict):
        raise ImportError_(NO_ES_PARTIDA)
    if "format" in info and (info["format"] != "comunitat-del-anell" or info.get("versio") != 1):
        raise ImportError_(NO_ES_PARTIDA)
    docs = check_docs(info.get("docs"))
    name = camp_name(docs, "") or str(info.get("nom") or "")[:80] or "Partida importada"
    if any(c["name"] == name for c in list_campaigns()):
        name = f"{name} (importada)"
    docs["campaign/main"] = {**(docs.get("campaign/main") or {}), "name": name}
    cid = slugify(name)
    write_json(camp_file(cid), {"docs": docs})
    return cid


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


def session_snapshot(sess):
    return {"me": {"uid": sess["uid"], "dm": True}, "campaign": state["active"],
            "epoch": state["epoch"], "revision": state["revision"], "docs": snapshot()}


def broadcast(paths):
    with lock:
        for c in list(clients):
            for p in paths:
                c.send("doc", {"path": p, "data": get_doc(p), "epoch": state["epoch"], "revision": state["revision"]})


def broadcast_event(kind, payload):
    with lock:
        for c in list(clients):
            c.send(kind, copy.deepcopy(session_snapshot(c.sess) if kind == "snapshot" else payload))


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
            out = {"taula": 1, "version": VERSION, "local": self._local()}
            if out["local"]:
                out["dades"] = str(DATA_DIR)
            return self._json(200, out)
        if route == "/api/invite":
            urls = lan_urls() or [f"http://localhost:{state['port']}"]
            return self._json(200, {"list": [{"url": u, "svg": qr_svg(u)} for u in urls]})
        sess = self._session()
        if route in ("/api/history", "/api/campaigns", "/api/snapshot", "/api/events", "/api/export") and not sess:
            return self._json(401, {"error": "Sessió no vàlida. Torna a entrar."})
        if route == "/api/history":
            with lock:
                return self._json(200, {"list": list(reversed(state["history"]))})
        if route == "/api/campaigns":
            with lock:
                return self._json(200, {"active": state["active"], "list": list_campaigns(), "trash": list_trash()})
        if route == "/api/snapshot":
            with lock:
                return self._json(200, session_snapshot(sess))
        if route == "/api/events":
            return self._events(sess)
        if route == "/api/export":
            return self._export()
        self._json(404, {"error": "No trobat"})

    def _local(self):
        """La petició ve d'aquest mateix ordinador (la finestra pròpia o un navegador en el servidor)?"""
        return self.client_address[0].startswith("127.") or self.client_address[0] == "::1"

    def _export(self):
        cid = (self._query().get("id") or [""])[0]
        with lock:
            if not re.fullmatch(r"[a-z0-9-]{1,60}", cid) or not camp_file(cid).exists():
                return self._json(404, {"error": "Aquesta partida ja no existeix."})
            if cid == state["active"]:
                save_now()
            name, blob = export_json(cid)
        fname = (slugify_plain(name) or "partida") + "-" + time.strftime("%Y%m%d") + ".json"
        # application/octet-stream perquè tots els navegadors i finestres el guarden com a fitxer
        return self._send(200, blob, "application/octet-stream",
                          {"Content-Disposition": f'attachment; filename="{fname}"', "Cache-Control": "no-store"})

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
            first = session_snapshot(sess)
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
        if route == "/api/import":
            return self._import()
        try:
            body = self._body()
        except Exception:  # noqa: BLE001
            return self._json(400, {"error": "Petició mal formada"})
        if not isinstance(body, dict):
            return self._json(400, {"error": "Petició mal formada"})
        if route == "/api/join":
            return self._join(body)
        sess = self._session()
        if not sess:
            return self._json(401, {"error": "Sessió no vàlida. Torna a entrar."})
        if route == "/api/write":
            return self._write(body, sess)
        if route == "/api/transaction":
            return self._transaction(body, sess)
        if route == "/api/campaigns":
            return self._campaigns(body)
        if route == "/api/history":
            return self._history(body)
        if route == "/api/carpeta":
            if not self._local():
                return self._json(403, {"error": "La carpeta de dades només es pot obrir des de l'ordinador principal."})
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            obrir_carpeta(DATA_DIR)
            return self._json(200, {"ok": True, "dades": str(DATA_DIR)})
        self._json(404, {"error": "No trobat"})

    def _import(self):
        if not self._session():
            return self._json(401, {"error": "Sessió no vàlida. Torna a entrar."})
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return self._json(400, {"error": NO_ES_PARTIDA})
        if n < 0 or n > MAX_IMPORT:
            return self._json(413, {"error": "El fitxer és massa gran."})
        data = self.rfile.read(n) if n else b""
        with lock:
            try:
                cid = import_campaign(data)
            except (ImportError_, ValueError, TypeError, RecursionError) as e:
                return self._json(400, {"error": str(e)})
            result = {"active": state["active"], "list": list_campaigns(), "imported": cid}
        return self._json(200, result)

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
            if body.get("epoch") != state["epoch"] or body.get("revision") != state["revision"] or body.get("camp") != state["active"]:
                return self._json(409, session_snapshot(sess))
            if body.get("camp") and body.get("camp") != state["active"]:
                return self._json(409, {"error": "S'ha obert una altra partida."})
            if not can_write(path, mode, sess):
                return self._json(403, {"error": "No tens permís per a canviar això."})
            if seg(path)[0] == "users":
                merged = deep_merge(get_doc(path) or {}, data) if mode == "update" else data
                state["users"][sess["uid"]] = str(merged.get("name") or "")[:40]
            else:
                docs = copy.deepcopy(state["docs"])
                if mode == "delete":
                    docs.pop(path, None)
                elif mode == "set":
                    docs[path] = data
                else:
                    docs[path] = deep_merge(docs.get(path) or {}, data)
                try:
                    check_docs(docs)
                except (ImportError_, TypeError, ValueError, RecursionError):
                    return self._json(400, {"error": NO_ES_PARTIDA})
                state["docs"] = docs
                if path == "game/state" and track_result(docs.get(path)):
                    save_history()
            dirty.set()
            state["revision"] += 1
            broadcast_event("snapshot", session_snapshot(sess))
        broadcast([path])
        return self._json(200, {"ok": True})

    def _transaction(self, body, sess):
        changes = body.get("changes")
        if not isinstance(changes, list) or not 1 <= len(changes) <= 10:
            return self._json(400, {"error": "Petició mal formada"})
        with lock:
            # Reintentar una petició ja confirmada no ha de repetir la jugada.
            request_id = body.get("requestId")
            if not isinstance(request_id, str) or not 1 <= len(request_id) <= 100:
                return self._json(400, {"error": "Petició mal formada"})
            key = (sess["uid"], request_id)
            if body.get("epoch") != state["epoch"] or body.get("camp") != state["active"]:
                return self._json(409, session_snapshot(sess))
            if key in completed_requests:
                return self._json(200, session_snapshot(sess))
            if body.get("revision") != state["revision"] or body.get("camp") != state["active"]:
                return self._json(409, session_snapshot(sess))
            docs = copy.deepcopy(state["docs"])
            for change in changes:
                if not isinstance(change, dict):
                    return self._json(400, {"error": "Petició mal formada"})
                path, data = change.get("path"), change.get("data")
                if not valid_path(path) or not isinstance(data, dict) or not can_write(path, "set", sess) or seg(path)[0] == "users":
                    return self._json(400, {"error": "Petició mal formada"})
                docs[path] = data
            try:
                check_docs(docs)
            except (ImportError_, TypeError, ValueError, RecursionError):
                return self._json(400, {"error": NO_ES_PARTIDA})
            previous, history = state["docs"], copy.deepcopy(state["history"])
            state["docs"] = docs
            try:
                history_changed = track_result(docs.get("game/state"))
                save_now()
            except OSError:
                state["docs"], state["history"] = previous, history
                return self._json(503, {"error": "No s'ha pogut guardar."})
            if history_changed:
                try:
                    save_history()
                except OSError as e:
                    # La jugada ja és durable; reintenta l'historial sense repetir-la.
                    dirty.set()
                    print(f"[!] No s'ha pogut guardar l'historial: {e}")
            state["revision"] += 1
            dirty.set()  # també activa les còpies periòdiques mentre es juga
            completed_requests[key] = True
            if len(completed_requests) > 1000:
                del completed_requests[next(iter(completed_requests))]
            broadcast_event("snapshot", session_snapshot(sess))
            return self._json(200, session_snapshot(sess))

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
        if cid and not re.fullmatch(r"[a-z0-9-]{1,100}" if action == "undelete" else r"[a-z0-9-]{1,60}", cid):
            return self._json(400, {"error": "Partida desconeguda."})
        switched = False
        with lock:
            if action == "undelete":
                f = TRASH_DIR / f"{cid}.json"
                if not cid or not f.is_file():
                    return self._json(404, {"error": "Aquesta partida ja no existeix."})
                try:
                    docs = check_docs(read_json(f).get("docs"))
                except (ImportError_, OSError, ValueError, TypeError):
                    return self._json(400, {"error": NO_ES_PARTIDA})
                restored = slugify(camp_name(docs, "Partida recuperada"))
                f.replace(camp_file(restored))
            elif action == "create":
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
                camp_file(cid).replace(TRASH_DIR / f"{cid}-{time.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3)}.json")
            elif action == "backups":
                if not camp_file(cid).exists():
                    return self._json(404, {"error": "Aquesta partida ja no existeix."})
                return self._json(200, {"id": cid, "list": list_backups(cid)})
            elif action == "backup":
                if not camp_file(cid).exists():
                    return self._json(404, {"error": "Aquesta partida ja no existeix."})
                if cid == state["active"]:
                    save_now()
                make_backup(cid, campaign_docs(cid), "ma")
                return self._json(200, {"id": cid, "list": list_backups(cid)})
            elif action == "restore":
                bid = str(body.get("backup") or "")
                bf = backup_dir(cid) / f"{bid}.json"
                if not camp_file(cid).exists() or not BACKUP_RE.fullmatch(bid) or not bf.exists():
                    return self._json(404, {"error": "Aquesta còpia ja no existeix."})
                try:
                    docs = check_docs(read_json(bf).get("docs"))
                except Exception:  # noqa: BLE001
                    return self._json(400, {"error": "La còpia està danyada."})
                make_backup(cid, campaign_docs(cid), "abans")     # per si de cas, una còpia del que hi havia
                if cid == state["active"]:
                    state["docs"] = docs
                    state["revision"] += 1
                    save_now()
                    switched = True
                else:
                    write_json(camp_file(cid), {"docs": docs})
            else:
                return self._json(400, {"error": "Acció desconeguda."})
            dirty.set()
            result = {"active": state["active"], "list": list_campaigns(), "trash": list_trash()}
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
    ap.add_argument("--navegador", action="store_true",
                    help="obri l'app al navegador, amb la finestreta de l'adreça i el QR, en compte de la finestra pròpia")
    ap.add_argument("--sense-finestra", action="store_true", help="no obri cap finestra: només el terminal")
    ap.add_argument("--sense-navegador", action="store_true", help="no obri el navegador en arrancar")
    ap.add_argument("--sense-qr", action="store_true", help="no mostra el codi QR al terminal")
    ap.add_argument("--idioma", choices=("ca", "es"), default="ca",
                    help="idioma de les finestres i els avisos: ca (valencià, per defecte) o es (castellà)")
    a = ap.parse_args()
    if a.dades.strip():
        set_data_dir(a.dades.strip())
    pantalla = not a.sense_finestra and hi_ha_pantalla()
    idioma = a.idioma
    state["port"] = a.port
    try:
        srv = Server(("0.0.0.0", a.port), Handler)
    except OSError:
        print(f"\n  El port {a.port} ja està en ús: hi ha un altre programa (potser La Comunitat ja oberta) escoltant-hi.\n"
              f"  Tanca'l, o arranca en un altre port:   python3 comunitat.py --port 9001\n")
        if pantalla:
            T = FINESTRA_TEXTOS[idioma]
            avis_finestra(T["port_t"], T["port_q"].format(p=a.port))
        sys.exit(1)
    load(a.partida.strip() or None)
    load_history()
    if track_result(state["docs"].get("game/state")):
        save_history()
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
    print()
    print(f"  Partida oberta:         {camp_name(state['docs'], state['active'])}")
    print(f"  Dades guardades a:      {DATA_DIR}")

    def mostra_qr():
        if urls and not a.sense_qr:
            print("\n  Escaneja aquest codi amb el mòbil per a entrar:\n")
            try:
                print(qr_terminal(urls[0]))
            except Exception:  # noqa: BLE001
                pass

    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        feta = False
        if pantalla and not a.navegador:
            print("\n  S'obri la finestra de La Comunitat. Tanca-la per a aturar-la.\n")
            feta = finestra_app(a.port, idioma)
        if not feta and pantalla and hi_ha_finestra():
            print("\n  Tanca la finestreta de La Comunitat per a aturar-la.\n")
            finestra_adreca(a.port, idioma, obrir_navegador=not a.sense_navegador)
            feta = True
        if not feta:
            mostra_qr()
            print("\n  Prem Ctrl+C per a aturar-la" + (" o tanca aquesta finestra" if os.name == "nt" else "") + ".\n")
            if pantalla and not a.sense_navegador:
                threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{a.port}")).start()
            while True:
                time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        srv.shutdown()
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
