#!/usr/bin/env python3
"""Fa els paquets de Linux de La Comunitat, sense dependències:

  dist/comunitat-del-anell_<versió>_all.deb     per a Debian, Ubuntu, Linux Mint…
  dist/LaComunitat-<versió>-linux.tar.gz     per a la resta (es descomprimeix i s'obri)

Ús:  python3 build.py
     python3 eines/paquet-linux.py [--versio 2.0] [--pdf CARPETA_AMB_ELS_MANUALS]
"""
import argparse
import gzip
import hashlib
import io
import re
import tarfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINUX = ROOT / "paquets" / "linux"
NOM = "comunitat-del-anell"
WEB = "https://jossanmar9.github.io/comunitat-del-anell/"
MANTENIDOR = "José Vicente Sanjuan <jossanmar9@users.noreply.github.com>"
ARA = int(time.time())


def versio_programa():
    m = re.search(r'^VERSION = "([^"]+)"', (ROOT / "src" / "servidor.py").read_text(encoding="utf-8"), re.M)
    return m.group(1)


def afig(tar, nom, dades, mode=0o644):
    info = tarfile.TarInfo(nom)
    info.size, info.mode, info.mtime = len(dades), mode, ARA
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    tar.addfile(info, io.BytesIO(dades))


def afig_carpeta(tar, nom):
    info = tarfile.TarInfo(nom)
    info.type, info.mode, info.mtime = tarfile.DIRTYPE, 0o755, ARA
    info.uid = info.gid = 0
    info.uname = info.gname = "root"
    tar.addfile(info)


def targz(fitxers, carpetes=()):
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb", mtime=ARA) as gz, tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT) as tar:
        for c in carpetes:
            afig_carpeta(tar, c)
        for nom, (dades, mode) in fitxers.items():
            afig(tar, nom, dades, mode)
    return buf.getvalue()


def ar(membres):
    """Un arxiu «ar», que és el que és un .deb per dins."""
    out = bytearray(b"!<arch>\n")
    for nom, dades in membres:
        out += f"{nom + '/':<16}{ARA:<12}{0:<6}{0:<6}{'100644':<8}{len(dades):<10}`\n".encode()
        out += dades
        if len(dades) % 2:
            out += b"\n"
    return bytes(out)


def documents(pdf_dir):
    docs = {n: (ROOT / n).read_bytes() for n in ("README.md", "README.es.md")}
    if pdf_dir:
        for pdf in sorted(Path(pdf_dir).glob("*.pdf")):
            docs[pdf.name] = pdf.read_bytes()
    return docs


def deb(versio, pdf_dir, eixida):
    programa = (ROOT / "comunitat.py").read_bytes()
    lib = f"usr/lib/{NOM}"
    doc = f"usr/share/doc/{NOM}"
    fitxers = {
        f"./{lib}/comunitat.py": (programa, 0o755),
        f"./{lib}/installat": (("Aquest fitxer indica que La Comunitat està instal·lada: les partides es guarden a\n"
                                "~/.local/share/comunitat-del-anell (o on diga --dades).\n").encode(), 0o644),
        f"./usr/bin/{NOM}": (f'#!/bin/sh\nexec python3 /{lib}/comunitat.py "$@"\n'.encode(), 0o755),
        f"./usr/share/applications/{NOM}.desktop": ((LINUX / f"{NOM}.desktop").read_bytes(), 0o644),
        f"./usr/share/icons/hicolor/128x128/apps/{NOM}.png": ((ROOT / "src" / "web" / "logo.png").read_bytes(), 0o644),
        f"./usr/share/pixmaps/{NOM}.png": ((ROOT / "logo.png").read_bytes(), 0o644),
        f"./{doc}/copyright": (copyright_deb(), 0o644),
    }
    for nom, dades in documents(pdf_dir).items():
        fitxers[f"./{doc}/{nom}"] = (dades, 0o644)
    carpetes = set()
    for nom in fitxers:
        parts = nom.split("/")[:-1]
        for i in range(1, len(parts) + 1):
            carpetes.add("/".join(parts[:i]) + "/")
    carpetes = sorted(carpetes)
    mida = sum(len(d) for d, _ in fitxers.values()) // 1024 + len(carpetes)
    control = f"""Package: {NOM}
Version: {versio}
Architecture: all
Maintainer: {MANTENIDOR}
Installed-Size: {mida}
Depends: python3 (>= 3.8), python3-gi, gir1.2-gtk-3.0, gir1.2-webkit2-4.1 | gir1.2-webkit2-4.0
Recommends: xdg-utils, python3-tk
Section: games
Priority: optional
Homepage: {WEB}
Description: Ajudant lliure per al joc de taula «El Destino de la Comunidad»
 Porta els comptes de les partides del joc cooperatiu «El Señor de los Anillos:
 El Destino de la Comunidad»: esperança, amenaça, torns, tirades de cerca i de
 batalla, objectius i historial. Un ordinador fa de servidor i la resta de la
 taula hi entra des del navegador, mòbils inclosos, sense Internet. En valencià
 i castellà. Projecte de fans no oficial; cal tindre el joc.
 .
 Ayudante libre para el juego de mesa «El Destino de la Comunidad», en castellano
 y valenciano.
""".encode()
    md5 = "".join(f"{hashlib.md5(d).hexdigest()}  {n[2:]}\n" for n, (d, _) in fitxers.items()).encode()
    control_tar = targz({"./control": (control, 0o644), "./md5sums": (md5, 0o644)}, ["./"])
    data_tar = targz(fitxers, carpetes)
    desti = eixida / f"{NOM}_{versio}_all.deb"
    desti.write_bytes(ar([("debian-binary", b"2.0\n"), ("control.tar.gz", control_tar), ("data.tar.gz", data_tar)]))
    return desti


def copyright_deb():
    return f"""Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: La Comunitat
Source: https://github.com/jossanmar9/comunitat-del-anell

Files: *
Copyright: 2026 Col·laboradors de La Comunitat
Comment: Unofficial fan project, not affiliated with Z-Man Games, Asmodee or
 Middle-earth Enterprises. "El Señor de los Anillos" and related names are
 trademarks of their respective owners. The example maps, logo and character
 portraits were generated with AI.
License: GPL-3.0-or-later
 On Debian systems, the full text of the GNU General Public License version 3
 can be found in /usr/share/common-licenses/GPL-3.
""".encode()


def tar_gz(versio, pdf_dir, eixida):
    carpeta = f"LaComunitat-{versio}-linux"
    fitxers = {
        f"{carpeta}/comunitat.py": ((ROOT / "comunitat.py").read_bytes(), 0o755),
        f"{carpeta}/comunitat-del-anell.sh": ((LINUX / "comunitat-del-anell.sh").read_bytes(), 0o755),
        f"{carpeta}/installa.sh": ((LINUX / "installa.sh").read_bytes(), 0o755),
        f"{carpeta}/comunitat-del-anell.desktop": ((LINUX / f"{NOM}.desktop").read_bytes(), 0o644),
        f"{carpeta}/logo.png": ((ROOT / "logo.png").read_bytes(), 0o644),
        f"{carpeta}/LICENSE": ((ROOT / "LICENSE").read_bytes(), 0o644),
    }
    for nom, dades in documents(pdf_dir).items():
        fitxers[f"{carpeta}/{'docs/' if nom.endswith('.pdf') else ''}{nom}"] = (dades, 0o644)
    carpetes = [f"{carpeta}/"] + ([f"{carpeta}/docs/"] if pdf_dir else [])
    desti = eixida / f"{carpeta}.tar.gz"
    desti.write_bytes(targz(fitxers, carpetes))
    return desti


def main():
    ap = argparse.ArgumentParser(description="Fa el .deb i el .tar.gz per a Linux")
    ap.add_argument("--versio", default=versio_programa())
    ap.add_argument("--pdf", help="carpeta amb els manuals en PDF per a incloure'ls")
    ap.add_argument("--eixida", default=str(ROOT / "dist"))
    a = ap.parse_args()
    if not (ROOT / "comunitat.py").exists():
        raise SystemExit("Falta comunitat.py: executa primer python3 build.py")
    eixida = Path(a.eixida)
    eixida.mkdir(parents=True, exist_ok=True)
    for f in (deb(a.versio, a.pdf, eixida), tar_gz(a.versio, a.pdf, eixida)):
        print(f"Fet: {f.relative_to(ROOT) if f.is_relative_to(ROOT) else f} ({f.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
