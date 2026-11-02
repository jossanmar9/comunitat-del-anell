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
La Comunitat (versió 3.0.0) — ajudant d'una persona per a portar les partides de
«El Señor de los Anillos: El Destino de la Comunidad», per a Windows i Linux.

Tot va en aquest únic fitxer: la pàgina de l'app, els mapes d'exemple i un petit servidor
que només escolta en aquest ordinador (127.0.0.1) i guarda els fitxers a la carpeta de dades.
L'app s'obri en una finestra pròpia (a Windows amb WebView2, a Linux amb WebKitGTK); si no es
pot, s'obri al navegador.

Ús (a Windows, canvia python3 per py, o fes doble clic a arrancar-windows.bat):
    python3 comunitat.py
    python3 comunitat.py --navegador            (l'app al navegador)
    python3 comunitat.py --dades CARPETA         (on es guarden les partides)

Les dades van al costat del programa, o a la carpeta de l'usuari si el programa està
instal·lat: cada partida a partides/<nom>.json, les partides acabades a historial.json i les
còpies de seguretat automàtiques a copies/<nom>/. Si poses una imatge mapa.jpg (o .png) a la
carpeta de dades, l'app la mostra al centre (també mapa-val.jpg i mapa-es.jpg, una per idioma).
"""
import argparse
import base64
import gzip
import json
import os
import re
import sys
import tempfile
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

VERSION = "3.0.0"
FROZEN = getattr(sys, "frozen", False)          # executable de Windows fet amb PyInstaller
DIR = Path(sys.executable).resolve().parent if FROZEN else Path(__file__).resolve().parent
INSTALLAT = (DIR / "installat").exists()       # el posen l'instal·lador de Windows i el paquet .deb
PORT = 8766
MAX_COS = 25 * 1024 * 1024                     # un mapa propi pot fer uns quants MB


def user_data_dir():
    """La carpeta de dades de l'usuari, per a quan el programa està instal·lat."""
    if os.name == "nt":
        return Path(os.environ.get("APPDATA") or Path.home() / "AppData" / "Roaming") / "LaComunitat"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "La Comunitat"
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share") / "comunitat-del-anell"


def set_data_dir(path):
    global DATA_DIR
    DATA_DIR = Path(path).expanduser().resolve()


set_data_dir(user_data_dir() if INSTALLAT else DIR)


__PERSISTENCIA__


# ---------------------------------------------------------------- el disc de l'app
# L'app (src/web/magatzem.js) fa tota la feina; ací només es llegeixen i s'escriuen fitxers JSON
# de la carpeta de dades, i només aquests:
RUTA_RE = re.compile(r"(?:(?:partides|partides/esborrades|copies/[a-z0-9-]{1,60})/[a-z0-9][a-z0-9._-]{0,120}\.json"
                     r"|historial\.json|comunitat\.json|mapa\.json)")
CARPETA_RE = re.compile(r"partides|partides/esborrades|copies/[a-z0-9-]{1,60}")
lock = threading.Lock()


class DiscError(Exception):
    pass


def ruta(text, carpeta=False):
    if not isinstance(text, str) or not (CARPETA_RE if carpeta else RUTA_RE).fullmatch(text):
        raise DiscError("Ruta no vàlida.")
    return DATA_DIR.joinpath(*text.split("/"))


def disc(op, cos):
    with lock:
        if op == "llig":
            f = ruta(cos.get("ruta"))
            if not f.is_file():
                return {"obj": None}
            try:
                return {"obj": json.loads(f.read_text(encoding="utf-8"))}
            except ValueError:
                # Un fitxer danyat no es sobreescriu: es guarda a part i es tracta com si no hi fóra.
                f.replace(f.with_name(f.name + ".danyat"))
                print(f"[!] {f.name} estava danyat; l'he guardat com a {f.name}.danyat.")
                return {"obj": None}
        if op == "escriu":
            obj = cos.get("obj")
            if not isinstance(obj, (dict, list)):
                raise DiscError("Dades no vàlides.")
            atomic_json(ruta(cos.get("ruta")), obj)
            return {}
        if op == "llista":
            d = ruta(cos.get("carpeta"), carpeta=True)
            if not d.is_dir():
                return {"list": []}
            return {"list": [{"nom": f.name, "ts": int(f.stat().st_mtime * 1000)} for f in d.iterdir()
                             if f.is_file() and f.suffix == ".json"]}
        if op == "esborra":
            f = ruta(cos.get("ruta"))
            if f.is_file():
                f.unlink()
            return {}
        if op == "mou":
            de, a = ruta(cos.get("ruta")), ruta(cos.get("a"))
            if not de.is_file():
                raise DiscError("Aquesta partida ja no existeix.")
            if a.exists():
                raise DiscError("Ja hi ha una partida amb aquest nom.")
            a.parent.mkdir(parents=True, exist_ok=True)
            de.replace(a)
            return {}
    raise DiscError("Acció desconeguda.")


def baixades():
    """La carpeta Baixades de l'usuari (on van les partides exportades)."""
    if os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders") as k:
                return Path(winreg.QueryValueEx(k, "{374DE290-123F-4565-9164-39C4925E467B}")[0])
        except OSError:
            return Path.home() / "Downloads"
    import subprocess
    try:
        d = subprocess.run(["xdg-user-dir", "DOWNLOAD"], capture_output=True, text=True, timeout=5).stdout.strip()
        if d and Path(d) != Path.home():
            return Path(d)
    except (OSError, subprocess.SubprocessError):
        pass
    for nom in ("Baixades", "Descargas", "Downloads"):
        if (Path.home() / nom).is_dir():
            return Path.home() / nom
    return Path.home()


def desa(nom, text):
    """Guarda una partida exportada a Baixades, sense sobreescriure res. Torna on l'ha guardada."""
    if not isinstance(nom, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,120}\.json", nom) or not isinstance(text, str):
        raise DiscError("Dades no vàlides.")
    d = baixades()
    d.mkdir(parents=True, exist_ok=True)
    base, ext = os.path.splitext(nom)
    f, n = d / nom, 1
    while f.exists():
        n += 1
        f = d / f"{base} ({n}){ext}"
    f.write_text(text, encoding="utf-8")
    return f


# ---------------------------------------------------------------- mapa
MAP_EXTS = (("jpg", "image/jpeg"), ("jpeg", "image/jpeg"), ("png", "image/png"), ("webp", "image/webp"))


def map_image(lang):
    """El mapa de la carpeta de dades (per idioma o general) o, si no n'hi ha, el d'exemple."""
    for d in dict.fromkeys((DATA_DIR, DIR)):
        for name in (f"mapa-{lang}", "mapa"):
            for ext, ctype in MAP_EXTS:
                f = d / f"{name}.{ext}"
                if f.is_file():
                    return f.read_bytes(), ctype
    return MAPES[lang], "image/jpeg"


__FINESTRA__


# ---------------------------------------------------------------- HTTP (només per a aquest ordinador)
class Handler(BaseHTTPRequestHandler):
    server_version = "Comunitat/" + VERSION
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype, extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8",
                   {"Cache-Control": "no-store"})

    def _host_ok(self):
        """Només s'accepten peticions a aquest mateix ordinador (evita que una web de fora hi arribe
        fent-se passar per localhost)."""
        port = self.server.server_address[1]
        return (self.headers.get("Host") or "") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def do_GET(self):
        if not self._host_ok():
            return self._json(403, {"error": "No permés."})
        route = self.path.split("?")[0]
        if route in ("/", "/index.html"):
            return self._send(200, PAGE_BYTES, "text/html; charset=utf-8",
                              {"Cache-Control": "no-store", "Content-Security-Policy": "frame-ancestors 'none'"})
        if route == "/mapa":
            lang = "es" if (parse_qs(urlparse(self.path).query).get("lang") or ["val"])[0] == "es" else "val"
            body, ctype = map_image(lang)
            return self._send(200, body, ctype, {"Cache-Control": "no-cache"})
        if route == "/api/hola":
            return self._json(200, {"comunitat": 3, "versio": VERSION, "dades": str(DATA_DIR)})
        self._json(404, {"error": "No trobat"})

    def do_POST(self):
        # La capçalera X-Comunitat fa que una pàgina d'una altra web no puga fer aquestes peticions.
        if not self._host_ok() or self.headers.get("X-Comunitat") != "1":
            return self._json(403, {"error": "No permés."})
        n = int(self.headers.get("Content-Length") or 0)
        if n > MAX_COS:
            return self._json(413, {"error": "El fitxer és massa gran."})
        try:
            cos = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(cos, dict):
                raise ValueError
        except ValueError:
            return self._json(400, {"error": "Petició mal formada"})
        route = self.path.split("?")[0]
        try:
            if route == "/api/disc":
                return self._json(200, disc(cos.get("op"), cos))
            if route == "/api/desa":
                return self._json(200, {"cami": str(desa(cos.get("nom"), cos.get("text")))})
            if route == "/api/carpeta":
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                obrir_carpeta(DATA_DIR)
                return self._json(200, {"ok": True})
        except DiscError as e:
            return self._json(400, {"error": str(e)})
        except OSError as e:
            print(f"[!] No s'ha pogut guardar: {e}")
            return self._json(503, {"error": "No s'ha pogut guardar."})
        self._json(404, {"error": "No trobat"})


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        if isinstance(sys.exc_info()[1], (BrokenPipeError, ConnectionResetError, ConnectionAbortedError)):
            return
        super().handle_error(request, client_address)


def arranca_servidor(port):
    """El port de sempre (8766); si està ocupat per un altre programa, un de lliure."""
    for p in (port, 0):
        try:
            return Server(("127.0.0.1", p), Handler)
        except OSError:
            continue
    raise OSError("No hi ha cap port lliure.")


def main():
    for name in ("stdout", "stderr"):  # l'executable de Windows no té terminal
        if getattr(sys, name) is None:
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))
    for stream in (sys.stdout, sys.stderr):  # les consoles de Windows potser no parlen UTF-8
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:  # noqa: BLE001
            pass
    ap = argparse.ArgumentParser(description="La Comunitat: ajudant per a «El Destino de la Comunidad»")
    ap.add_argument("--dades", default=os.environ.get("COMUNITAT_DADES", ""),
                    help="carpeta on es guarden les partides (per defecte, al costat del programa, "
                         "o a la carpeta de l'usuari si està instal·lat)")
    ap.add_argument("--navegador", action="store_true", help="obri l'app al navegador en compte de la finestra pròpia")
    ap.add_argument("--sense-finestra", action="store_true", help="no obri res: només el servidor, al terminal")
    ap.add_argument("--sense-navegador", action="store_true", help="amb --navegador, no l'obri en arrancar")
    ap.add_argument("--port", type=int, default=PORT, help=f"port local (per defecte, {PORT})")
    ap.add_argument("--idioma", choices=("ca", "es"), default="ca",
                    help="idioma dels avisos de les finestres: ca (valencià, per defecte) o es (castellà)")
    # Opcions de la v2 (QR i sala) que ja no fan res; s'accepten perquè no fallen els accessos d'abans
    ap.add_argument("--sense-qr", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--partida", help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.dades.strip():
        set_data_dir(a.dades.strip())
    pantalla = not a.sense_finestra and hi_ha_pantalla()
    T = FINESTRA_TEXTOS[a.idioma]
    try:
        bloqueig = DataDirectoryLock(DATA_DIR)
    except OSError:
        print("\n  La Comunitat ja està oberta amb aquesta carpeta de dades.\n")
        if pantalla:
            avis_finestra(T["oberta_t"], T["oberta_q"])
        return 1
    try:
        migra_v2(DATA_DIR)
        srv = arranca_servidor(a.port)
    except OSError as e:
        print(f"\n  No s'ha pogut arrancar: {e}\n")
        if pantalla:
            avis_finestra(T["error_t"], str(e))
        bloqueig.close()
        return 1
    port = srv.server_address[1]
    url = f"http://127.0.0.1:{port}/"
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:  # en apagar l'ordinador o tancar la sessió, es tanca igual que amb Ctrl+C
        import signal
        signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt()))
    except Exception:  # noqa: BLE001
        pass
    print(f"\n  La Comunitat (versió {VERSION}) està en marxa.")
    print(f"  Dades guardades a: {DATA_DIR}")
    try:
        feta = False
        if pantalla and not a.navegador:
            print("\n  S'obri la finestra de La Comunitat. Tanca-la per a aturar-la.\n")
            feta = finestra_app(url, a.idioma)
        if not feta:
            if pantalla and not a.sense_navegador:
                threading.Timer(0.8, lambda: webbrowser.open(url)).start()
            print(f"\n  Obri {url} al navegador d'aquest ordinador.")
            if pantalla and hi_ha_finestra():
                finestra_reserva(url, a.idioma)
            else:
                print("  Prem Ctrl+C per a aturar-la" + (" o tanca aquesta finestra" if os.name == "nt" else "") + ".\n")
                while True:
                    time.sleep(3600)
    except KeyboardInterrupt:
        pass
    finally:
        srv.shutdown()
        bloqueig.close()
        print("\n  Fins la pròxima!\n")
    return 0


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
    sys.exit(main())
