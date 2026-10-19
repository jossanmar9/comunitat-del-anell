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
La Comunitat (versió 1.4) — servidor local per a portar partides de
«El Señor de los Anillos: El Destino de la Comunidad».

Tot va en aquest únic fitxer: el servidor i la pàgina web. Un ordinador
l'executa i la resta s'hi connecta des del navegador. És cooperatiu: tothom
pot fer canvis, no hi ha màster.

Ús (a Windows, canvia python3 per py, o fes doble clic a arrancar-windows.bat):
    python3 comunitat.py
    python3 comunitat.py --partida "Divendres"
    python3 comunitat.py --port 9001

Cada partida es guarda en un fitxer dins de la carpeta partides/.
Si poses una imatge mapa.jpg (o .png) al costat d'aquest fitxer, l'app la mostra al centre.
També pots posar mapa-val.jpg i mapa-es.jpg, un per idioma. Si no n'hi ha cap, mostra
mapa-exemple-val.jpg o mapa-exemple-es.jpg segons l'idioma de qui mira.

En arrancar mostra un codi QR: escaneja'l amb el mòbil per a entrar sense escriure l'adreça.
Les partides acabades (guanyades o perdudes) es guarden a historial.json.
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

VERSION = "1.4"
FROZEN = getattr(sys, "frozen", False)          # executable de Windows fet amb PyInstaller
DIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
BUNDLE = Path(getattr(sys, "_MEIPASS", DIR))     # on van els mapes d'exemple dins de l'.exe
HIST = DIR / "historial.json"   # partides acabades
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
    "history": [],     # partides acabades
    "port": 8766,
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
    """Apunta o desapunta una partida acabada quan canvia game/state (caller holds the lock)."""
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


# ---------------------------------------------------------------- QR (sense dependències)
# Codificador QR mínim (mode byte, correcció M, versions 1-10), basat en l'algorisme
# de l'especificació ISO/IEC 18004. N'hi ha prou per a una adreça com http://192.168.1.40:8766.
_QR_ECC_M = (None, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26)   # codewords de correcció per bloc
_QR_BLOCKS_M = (None, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5)          # blocs


def _gf_mul(x, y):
    z = 0
    for i in reversed(range(8)):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_divisor(degree):
    res = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(len(res)):
            res[j] = _gf_mul(res[j], root)
            if j + 1 < len(res):
                res[j] ^= res[j + 1]
        root = _gf_mul(root, 0x02)
    return res


def _rs_remainder(data, divisor):
    res = [0] * len(divisor)
    for b in data:
        factor = b ^ res.pop(0)
        res.append(0)
        for i, coef in enumerate(divisor):
            res[i] ^= _gf_mul(coef, factor)
    return res


def _qr_raw_modules(ver):
    r = (16 * ver + 128) * ver + 64
    if ver >= 2:
        na = ver // 7 + 2
        r -= (25 * na - 10) * na - 55
        if ver >= 7:
            r -= 36
    return r


def qr_matrix(text):
    """Torna una llista de files de booleans (True = mòdul fosc), sense marge."""
    data = text.encode("utf-8")
    for ver in range(1, 11):
        cap = _qr_raw_modules(ver) // 8 - _QR_ECC_M[ver] * _QR_BLOCKS_M[ver]
        cbits = 8 if ver <= 9 else 16
        if 4 + cbits + 8 * len(data) <= cap * 8:
            break
    else:
        raise ValueError("text massa llarg per al QR")
    bits = []

    def put(val, n):
        bits.extend((val >> i) & 1 for i in reversed(range(n)))
    put(0b0100, 4)
    put(len(data), cbits)
    for b in data:
        put(b, 8)
    put(0, min(4, cap * 8 - len(bits)))
    put(0, (-len(bits)) % 8)
    words = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = 0xEC
    while len(words) < cap:
        words.append(pad)
        pad ^= 0xEC ^ 0x11
    # blocs i correcció d'errors
    nblocks, ecl = _QR_BLOCKS_M[ver], _QR_ECC_M[ver]
    raw = _qr_raw_modules(ver) // 8
    nshort = nblocks - raw % nblocks
    short_len = raw // nblocks
    div = _rs_divisor(ecl)
    blocks, k = [], 0
    for i in range(nblocks):
        dat = words[k:k + short_len - ecl + (0 if i < nshort else 1)]
        k += len(dat)
        ecc = _rs_remainder(dat, div)
        if i < nshort:
            dat = dat + [0]
        blocks.append(dat + ecc)
    final = []
    for i in range(len(blocks[0])):
        for j, blk in enumerate(blocks):
            if i != short_len - ecl or j >= nshort:
                final.append(blk[i])
    # matriu
    size = ver * 4 + 17
    mod = [[False] * size for _ in range(size)]
    fun = [[False] * size for _ in range(size)]

    def setf(x, y, dark):
        mod[y][x] = bool(dark)
        fun[y][x] = True
    for i in range(size):
        setf(6, i, i % 2 == 0)
        setf(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                x, y = cx + dx, cy + dy
                if 0 <= x < size and 0 <= y < size:
                    setf(x, y, max(abs(dx), abs(dy)) not in (2, 4))
    if ver > 1:
        na = ver // 7 + 2
        step = (ver * 8 + na * 3 + 5) // (na * 4 - 4) * 2
        pos = list(reversed([size - 7 - i * step for i in range(na - 1)] + [6]))
        for i, ax in enumerate(pos):
            for j, ay in enumerate(pos):
                if (i == 0 and j == 0) or (i == 0 and j == na - 1) or (i == na - 1 and j == 0):
                    continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3):
                        setf(ax + dx, ay + dy, max(abs(dx), abs(dy)) != 1)

    def draw_format(mask):
        d = (0 << 3) | mask          # nivell M = 0b00
        rem = d
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        b = ((d << 10) | rem) ^ 0x5412
        bit = lambda i: (b >> i) & 1  # noqa: E731
        for i in range(6):
            setf(8, i, bit(i))
        setf(8, 7, bit(6))
        setf(8, 8, bit(7))
        setf(7, 8, bit(8))
        for i in range(9, 15):
            setf(14 - i, 8, bit(i))
        for i in range(8):
            setf(size - 1 - i, 8, bit(i))
        for i in range(8, 15):
            setf(8, size - 15 + i, bit(i))
        setf(8, size - 8, True)
    draw_format(0)
    if ver >= 7:
        rem = ver
        for _ in range(12):
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
        b = (ver << 12) | rem
        for i in range(18):
            a, c = size - 11 + i % 3, i // 3
            setf(a, c, (b >> i) & 1)
            setf(c, a, (b >> i) & 1)
    i = 0
    right = size - 1
    while right >= 1:
        if right == 6:
            right = 5
        for vert in range(size):
            for j in range(2):
                x = right - j
                y = size - 1 - vert if ((right + 1) & 2) == 0 else vert
                if not fun[y][x] and i < len(final) * 8:
                    mod[y][x] = bool((final[i >> 3] >> (7 - (i & 7))) & 1)
                    i += 1
        right -= 2
    masks = (
        lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0,
        lambda x, y: (x + y) % 3 == 0, lambda x, y: (x // 3 + y // 2) % 2 == 0,
        lambda x, y: x * y % 2 + x * y % 3 == 0, lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
        lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0)

    def apply(m):
        for y in range(size):
            for x in range(size):
                if not fun[y][x] and masks[m](x, y):
                    mod[y][x] = not mod[y][x]

    def penalty():
        p = 0
        for grid in (mod, list(map(list, zip(*mod)))):
            for row in grid:
                run, prev = 0, None
                for v in row:
                    if v == prev:
                        run += 1
                    else:
                        if run >= 5:
                            p += run - 2
                        run, prev = 1, v
                if run >= 5:
                    p += run - 2
                s = "".join("1" if v else "0" for v in row)
                p += 40 * (s.count("10111010000") + s.count("00001011101"))
        for y in range(size - 1):
            for x in range(size - 1):
                if mod[y][x] == mod[y][x + 1] == mod[y + 1][x] == mod[y + 1][x + 1]:
                    p += 3
        dark = sum(map(sum, mod))
        p += abs(dark * 20 - size * size * 10) // (size * size) * 10
        return p
    best, best_p = 0, None
    for m in range(8):
        apply(m)
        draw_format(m)
        pen = penalty()
        if best_p is None or pen < best_p:
            best, best_p = m, pen
        apply(m)
    apply(best)
    draw_format(best)
    return mod


def qr_svg(text, scale=8, quiet=4):
    m = qr_matrix(text)
    n = len(m) + quiet * 2
    path = "".join(f"M{x + quiet},{y + quiet}h1v1h-1z" for y, row in enumerate(m) for x, v in enumerate(row) if v)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" width="{n * scale}" height="{n * scale}" '
            f'shape-rendering="crispEdges" role="img"><rect width="{n}" height="{n}" fill="#fff"/>'
            f'<path d="{path}" fill="#000"/></svg>')


def qr_terminal(text, quiet=2):
    """El QR amb mitjos blocs: negre sobre blanc forçat amb colors ANSI."""
    m = qr_matrix(text)
    size = len(m)
    get = lambda x, y: 0 <= x < size and 0 <= y < size and m[y][x]  # noqa: E731
    lines = []
    for y in range(-quiet, size + quiet, 2):
        row = ""
        for x in range(-quiet, size + quiet):
            top, bot = get(x, y), get(x, y + 1)
            row += "█" if top and bot else "▀" if top else "▄" if bot else " "
        lines.append("  \x1b[30;107m" + row + "\x1b[0m")
    return "\n".join(lines)


def lan_urls():
    return [f"http://{ip}:{state['port']}" for ip in lan_addresses()]


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
            from urllib.parse import parse_qs, urlparse
            lang = (parse_qs(urlparse(self.path).query).get("lang") or ["val"])[0]
            lang = "es" if lang == "es" else "val"
            exts = (("jpg", "image/jpeg"), ("jpeg", "image/jpeg"), ("png", "image/png"), ("webp", "image/webp"))
            cands = [(f"mapa-{lang}.{e}", c) for e, c in exts] + [(f"mapa.{e}", c) for e, c in exts]
            cands += [(f"mapa-exemple-{lang}.jpg", "image/jpeg"), ("mapa-exemple-val.jpg", "image/jpeg")]
            files = [(DIR / n, c) for n, c in cands] + [(BUNDLE / n, c) for n, c in cands if "exemple" in n]
            for f, ctype in files:
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
        if route == "/api/invite":
            urls = lan_urls() or [f"http://localhost:{state['port']}"]
            return self._json(200, {"list": [{"url": u, "svg": qr_svg(u)} for u in urls]})
        if route == "/api/history":
            sess = self._session()
            if not sess:
                return self._json(401, {"error": "Sessió no vàlida"})
            with lock:
                return self._json(200, {"list": list(reversed(state["history"]))})
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
        if route == "/api/history":
            return self._history(body)
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
                if path == "game/state" and track_result(docs.get(path)):
                    save_history()
            dirty.set()
        broadcast([path])
        return self._json(200, {"ok": True})

    def _history(self, body):
        sess = self._session()
        if not sess:
            return self._json(401, {"error": "Sessió no vàlida. Torna a entrar."})
        hid = str(body.get("id") or "")
        with lock:
            if body.get("action") == "delete":
                state["history"] = [h for h in state["history"] if h["id"] != hid]
                save_history()
            return self._json(200, {"list": list(reversed(state["history"]))})

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
    if os.name == "nt":
        os.system("")  # activa els colors ANSI de la consola de Windows (per al QR)
    ap = argparse.ArgumentParser(description="Servidor local de La Comunitat")
    ap.add_argument("--port", type=int, default=8766)
    ap.add_argument("--master-password", default=os.environ.get("TAULA_MASTER_PASSWORD", ""))
    ap.add_argument("--partida", default="", help="nom de la partida que s'obri en arrancar (la crea si no existeix)")
    ap.add_argument("--sense-qr", action="store_true", help="no mostra el codi QR en arrancar")
    ap.add_argument("--sense-navegador", action="store_true", help="(.exe) no obri el navegador en arrancar")
    a = ap.parse_args()
    state["port"] = a.port
    MASTER_PASSWORD = secrets.token_hex(8)  # cooperative game: nobody uses it
    try:
        srv = Server(("0.0.0.0", a.port), Handler)
    except OSError:
        print(
            f"\n  El port {a.port} ja està en ús: hi ha un altre programa (potser La Comunitat ja oberta) escoltant-hi.\n"
            f"  Tanca'l, o arranca en un altre port:   python3 comunitat.py --port 9001\n")
        if FROZEN:
            input("  Prem Intro per a tancar.")
        sys.exit(1)
    load(a.partida.strip() or None)
    load_history()
    threading.Thread(target=saver, daemon=True).start()
    print(f"\n  La Comunitat (versió {VERSION}) està en marxa.\n")
    print(f"  En aquest ordinador:   http://localhost:{a.port}")
    urls = lan_urls()
    for u in urls:
        print(f"  Des de la xarxa:       {u}")
    if urls and not a.sense_qr:
        print("\n  Escaneja aquest codi amb el mòbil per a entrar:\n")
        try:
            print(qr_terminal(urls[0]))
        except Exception:  # noqa: BLE001
            pass
    print()
    print(f"  Partida oberta:         {camp_name(state['docs'], state['active'])}")
    print(f"  Partides guardades a:   {CAMP_DIR}")
    print("\n  Prem Ctrl+C per a aturar-lo" + (" o tanca aquesta finestra" if FROZEN else "") + ".\n")
    if FROZEN and not a.sense_navegador:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://localhost:{a.port}")).start()
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
j8d+CZHGbhamIdlqpulBsQdrZpBcVUzMECZiC963RrO+2KPelF/R37W21jxiZAWuVaX3DvA8R50f1nV9tjKm+tAAO0R6aP66fsKz
GV154gWFniHSyB6EaiPSoVA6G2oEh5eVhG7u8oIYdPoaMZphUSD8F4jWMdHWbQkDKjUbc1BZAScFeMgyA76EpQWYhJXeKofvmoPl
MCIsgAkEYMyufLn9zC5hZYpfCWmmX746l7huHvCeOWwzuZ/fmIxMeSYH0p76AK4AW6g3t6IH2jA2CKgkoYAP1ZW4kW6Xalf25/17
g8DH+aVVyrL8t3/7p//6n/4LWOVJ9v7/jdn9/tvqrcv/Kzv2+1BvyfZXlv/V/Z8+Q951/wX893X/6b909dD+teTdv/3TtOTpOAx5
uv3TX9WSF//2T9W2TevfQbAYh23913Icyy5Ppnr913Ts/+n/v23Xd/91+o8N/0qXcV3HpS7r4f+tkXW7u3yt3qT0/8sBgOm6Iv/n
Iunr7v63T5eXS34nf3/Ps/uXs6y2/wX6FwyC/jP0L/g/Xol/vJLvK/yn/H/4/9gOcNm//2Mr/P+1TtYB4e0qgB/Krl6rfzT9v7zb
/39Z/zbxP2T1OnXJ/W/rmUx/OugfZ/Rf/xP4P//Fr1vd/fUe9n/7f/71P075Uib9f/t//FX/tdXDlvxP//qX1tXpf/u/D2md/CVa
2t/Qf4X+Ni5/65ItX/71r/8Z/NOEltzjvv39r2T4q+66va+Hd232V5r0U1KXw19dnpX58tf/+n/9v/31Jwzet13d5n8lf/XJsK/p
Uk/bX/8Y9b9+yZD9y1/nK7F/JUue/DUOf23VGxt5sf3LWz+r0/yvbUnu/33FO1TV9tf/+Bu3bez/+scI/Vk1VeOQr+/BW8l7Rn/9
7r+y5P6Xt5nk3Wj522/ch+xPafrursu7fzTyRuHw580/Turvyzhu/5f/9Ndff/vbr/z7P/M0xzLsf36X1n0pkjT/+z8LGP/hkP+u
6G/IW+/z1qP/FL6h8/d/Rj4wC0N/Fvv97ZC//zMh4B/sHwVvbL2NsNiHof6P5T8tfCiKxfn//I89J2maD9vf/5li/zT0n/+Pkn9v
XGB4gfv8d6XrWLyV30KUEf69gXLs3p1+EBKD/3FQf5b/o5oAcQKD/Hu1XzeObz2aRRhY+Pd6f5ZRnvigxJ/lbV+G92wY7EMw//vy
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
dGlbjRrb/TCaqpTLpWz2tBid5ofqutCpV7RqEoRFrZeIHmaR3DD0JM676izVTyxb8dgyO58K22Xeqi3VqZXYjU/N/HEi5fP1x166
3O3VUooxD4X2w1VGCO13nYTZqQ0rZdCPpVCv3t3t7EM6YQ9CiWUPlIFqdVhubQuHxXxeCS0PyyFArOjZKNjN7TaajBW00DEq7FrV
9eN8I0dnlclTadTXNpntIlEKVWdnKQt1yPNOPLSVu7DSsrlOttHWpmOjqww3+V1mo5XG0UK+yg+nHUWLTlaPoWJtHN202o1KOb8Q
j+XHx8ZTvz6rnSKP0VlyrU4NybYzUrY5K63qG5Fvlsad4rl1TIxypU58NVb2fb6wmeraWE23jlHdPNvb2FNX7kfjiYzUSUTUw3xw
1qVSIREqrVI76TiLm2k7e2wk9t3kIFeftRbxqsiXTsWyXK2Lk3FVj8a6w4qxEMdPomZP193VzBCz9cKTZSrzojWcFYYAVof9gZhK
xezSZh7b7wrLdiur5LIA+NRNax/vWOXcU29f7sV6Wmgii/l9KCSfVs1QLb0VszJvzUuGcEq3SrWxaFm1XEhrb6KSle4M0ql9PTRo
zHtqvxDvr9o1sVK1JjPYE4+DpqKXCpPseLOsRaujvPq40YrZfZLX9ZqqrIfladTu2YnxtlFej3fDSiqbOy8rjXU6OW7G1pl4f1pc
TlM19bwpqavema88DYFdiyGtnJw/buVJJb9/bEzX8nZlThVVOA6Sm/VkddoMmq1aKZR7rAjqVquFau14daO0M1Kzjl6MdjWmHnD9
LOu5dOKpEN2Zs2lUrLX35Wq8HU3ss0rS3icG09N5Fq+3tvb5HIpv0mOruzbjrdNTSG9ka7UUXtS5X+T29fVA6p7tWrOc0aJGuyDs
MMbxmMtsZuP6UY3Yy12kVcvE1JpujxrKeiSMZq3H4nq0aI60dEOtaJnTOpJrRZu1TPx8OMa6YlafR9KpU9ZWj5HOk9SuRKLLZMpM
JELbPKgA1aL1KMb4vdydLiNGey6LtUVltheGiURqU+sP9+Y8FjskHpWpfQolz93Iptoq5RLi+rjpZduPrfbx0SwKcqzahzUsqrtk
txtZnqrytj+Tz4PapLbryVLpnMnVyjt9e8rEmv3OQlpNhEWqW+U3qZaSDs02cm6QsafVRmJ1FDqd8zaz2zTi4uN+WtoarfxjzS5P
iodVTW5P020FNKLVdrTdtqOn9lOFV8dVZcibymDQ1DKbpLESDUkYtATxUJuJ6cymHNqdK0szpQ5rvWN9XTvW5KptT7LdihzLtWMt
cdad8KND9XB4EoqpnF4XC/I8kdyv9EantgEEeC51Q6HZtNTNSEd7MeO1Wa2xOEVaWjYGOoHZ7W/72jG+EAqzJ0U9gMax1NfKKdqL
zrtTZXDaJPetdURVzd7THlBgP2br8hgA+iqXCp270eVsMsDfhlqAejWr5yK5crFYrJWTPVWP9JqtaWhSS6ihQq91Ts/6i7QaycTX
pdP2HOnxSqRuJs7rcqeQlrsbuWIb4kSo2OXCMTlPhuSNMDTm42pTL5TL+Qpgu/amOE02K2pFWs2bsrCItcVqa2WvR7t6anKa8pWp
rG6TJ8FIFNJ6eSYMO63ZNj4+ZEZGWt4vH5uF0awai61m7dpG53tnuWEW0+V4dqx1Rv38vKcPo+N6v96XRrNRehUvnbXkNjVrVmuP
0ujplAzVlcaoPzWq6cqeP2WN8eTxLBd6WqZSOlnr3TxzbpyE/irVNtT9uDA85YRkLabE8Mc+24eZPNrw5nFYbBnJZDSbO4J04w/2
NnocKM0NwLRiLa4q8uk4nZqTRFo61Cx7Eh2dmlI5MxxNn3q1zDmnjKKD42SnaJ3hDnbxxWkkdteJgzJcyon6U9/cN1U7F9+cswl5
IpmN46QjZrs5PO6s5GvpUzmVX2bkXisR2XWK2YHVyZ3iiX2inYyNj1pJW++7dvdxoj+V1vV6XuFTx85gcVb7pUN9XzbLcUCrkZHd
5QfDVVKEMd72uz3YF63kObN/WgHuHsSFtVDQJ3yqhhcaz7bL8lwYTJWnUH9QXFlnYQRAra13OtHh4JjqRVu2pR7ndfNx3hyKenE9
LsoDda3XmnELxOLsadE3SoutHC+tW6CT11fbeKa1bVuqNDALvDBS1WRiuCuNZ0ojU4ttjVFlq2mqqfA9vRZf1vn4bBbNCtnGRmhn
tuenCL9uRo1is5lPVVWze97UFrCLZPfpTGxf0/abVmWhWU/7xfhcOC4ex7PJUrSij+PYKaZ2xaUaqsxLqZgUTWnZecayWtOJXt82
jooEUFPkZ/ajFBFTid1GD5lNNXTs5NaxcddOPx5bysAImcdlTi6G8mo3WrHFuQ6oLqLCghI6ueMxFjci1ahYmdYy++aykkhkqqO9
/pQrNGcNLV4DGS6o1Uqan02Kmjq3I92ovI/uuudO1BrJE/UYLR33YnQUGZzNUWFjbJqtRvkxq631fr2MV16MV229YrYTQrHRrywW
wOVa11SsvtJMHXLyoH/i+eJqdFj1xe3y1CpKzSTPn4V6M7ntj2snRRq1RgM9PxBS4+jOts1jN7bdHpqVQUyX+J2dn5VkM5E7N7O2
ZpnCIVfOR47FrWikRtN1NbTs1vj9WbRz4jBTUPO88NioKmOJjy3Ph4jZW0SWk2GiZVnbtFI8a+fCLCrXBsZMaQ/nGfnYmkfT69FT
+lEqKotuyWiY01ZZFfZzfvw0X3Zha88e01Ex35vo07pqpWP1WmJXEGuF9qSXbPGNg27XIuX1MpJIjFqhwmLQ5xurcfuolDvHiNnc
pFPqZh3fC6J6fIplpNpeWyxBwkq5Qdl6bAp9IapvtVloYZbs0zxZje5roUIslugfI7XT0Jxudz0xCjtHq1U5Zq2o9dg2KtLTbNGz
mmVt1OHnUiuZjNtKJj8sWkXt6XSY1xRRLM6Lp3qrJfF6exYPNXcZYRsfaiCa10Jd0vlTOzar6oBNR6muOcyfhmonvjWk1Wh2mh1K
nZ3RiT/OMjOpLZtHe3IcSjtrKUjlEp8UHhdGPJkdpJuLs1ava4rdUXlhmylbUtreTwCzDXhp1uhNUu3VonuuFeL1XT++61cByMS2
0ZRuhyxzPG5XNhFRt/v5/q6d6dZVM3TWE+On1PoctQf1pT0RnwwjPYokUzFYOJ1+dC/FsrnWMtGohrKbTF8EJdbIJpI9a1zsFmpL
cQn6TyWbVyMJaTTP5hrlSSqdS2YP44K43zQNMbPsjcujVDTXbuc2SnSzHJ1m83WjsYyL6eO0lzw/LVpyWhlZ6ixpZHKx4SFSL7Za
ofXKKvQPke7j4nw82dv61rCa+rirL2OaMhjWCjk9q233teqyYUqptJyZnE9zu9eW2yex3Z5biVKqMFSmarqzOY+bp1NMfEw/bdV4
KrVaVEfLxDjakOX4YSVF9/tkqxCb9kbVTaYF83+aFjPVpNiRM8bhNFxEqsWDchpEqv1iVz8rzVGq117IyjY6HI7krLBYNCZGOzUw
kplz6GhuxolMarNOW+YO2Uoftu32sDWpH4tj206k60/x3GwlnLRsZlvTjbXNpyCNF8Z8vJrMa7HmKsanDsNELy6coh1RCRkdsd+L
2CV5b1fKkVZGVydq5DA3k+tu5LGWifRiZr6X1YbrwqR8KG3jLfUxNGros3gr1Ve7oUh6Oltn0pKobXShvJknCkqltT32K8MFP2ul
9otFDgB0dNaZG3Z2lRBDogT4TY1tj/HioZfcb+OTYyR3GKT09vq8zkK120VICZWqg8y+PqvCEhcmw30VHTdiSNDX0VZd1rtLqbjq
tPrruJUpthrtx3rBSO8kvdOrdofy4SjxJt4nPOxOWk/Jnaw2EmovNq6NxDxsRqCGlzKwZ/f67fKmuuxXsj3JWhdrqYgk5ULLhl6t
m5NeJK+l9Owi3ztnKrGn6iSRfZzqw/Ry3cxJ0smylvaBTzxVK9uB0hlb2TMP2F2p8pJ91jO5xiwZiu+Gq6ZZMyxzltWFxiCyz/cX
ofryKDX2i3z/fDxGV5GxPez1Qnpe3rSreT7fqO2s01qxcpm9Ksm7WnsjZlLLp0kq21disdaej0baxazYk6eP5Yphgq4jgcTbPMmh
gnyK14Rp4ZDYKq25ta0+5czhrFcYrlei2EzUMqWRmbS6rWOSb6S0cbUS35kH2Osj56RZSRlWiE/xzVhtuplN9sd61SrHRuO2npeU
5rihVuX4sMwX6tlK6lFbSo+dsbrZzzczYb9X64Xu/inX68mN7H6BQvxUnTYG/SpsFk/lfsHaLI7zGK9394ma+LQEqJ6qdY4z06yG
kpF2ebYoWc1pa2PGaxnZaBw36UK9MSvEjrEnIamXC43QOZmYwHNNbNc3zfo2YrYi3c6+P50Y9WNGiMcH+kAQo+3HSKI/ykbKdTk7
4gupfTLz2DGOg/N5vwyNiqGuknwsPPIh5WCI1U1v2Ru2E021aJvW+cxnDEPeFyOq0e4mBmZjl25X5VNuoFRmVrSeVdKtsakXssVo
+zyaDvJjo1ZvpnPLoRwpJu1jWYrw7YNm1yrmupwP9bV1bym0F6VNKKRlF7GWut6a5253kioXT2MJpG5jmIpEjsPZvN60D5NZtj1t
rQAAFVaAfLd2ZBuaCc0OyKG1am6avfKoEs/Ys/jpdBqfZ9NI6Ji3l7X08ZAehZb9hNjRcv1Zf8w31qHiYFOXBWtQqscS8UZlmBwu
l71Os21tzYlUOERSvU2q0UZG6Y2ayalc5FuxrmDUSol5crfvxTbyrLw/L+1h+alULbXURKIY7SaF7TB70ubmspJ/MspaIZrdgOyd
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
eB/D3+lyDlLm/wEnpcbsVQEEAA==
"""))

if __name__ == "__main__":
    main()
