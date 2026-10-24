#!/bin/sh
# Afig La Comunitat al menú d'aplicacions de l'usuari (versió .tar.gz per a Linux).
#   ./installa.sh                 crea l'accés al menú
#   ./installa.sh --desinstalla   el lleva (les partides no s'esborren)
set -e
DIR="$(dirname "$(readlink -f "$0")")"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
FITXER="$APPS/comunitat-del-anell.desktop"

if [ "$1" = "--desinstalla" ]; then
  rm -f "$FITXER"
  command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" >/dev/null 2>&1 || true
  echo "S'ha llevat La Comunitat del menú. Les partides continuen a $DIR/partides."
  exit 0
fi

# La finestra pròpia necessita GTK i WebKitGTK; si no hi són, es fa servir la finestreta de Tk amb el navegador.
# Sense cap de les dues, l'accés obri un terminal, perquè es veja i es puga aturar.
WEBKIT=false
python3 -c "import gi; gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.1')
except ValueError:
    gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2" >/dev/null 2>&1 && WEBKIT=true
TERMINAL=false
[ "$WEBKIT" = true ] || python3 -c "import tkinter" >/dev/null 2>&1 || TERMINAL=true

chmod +x "$DIR/comunitat-del-anell.sh"
mkdir -p "$APPS"
sed -e "s|^Exec=.*|Exec=\"$DIR/comunitat-del-anell.sh\"|" \
    -e "s|^Icon=.*|Icon=$DIR/logo.png|" \
    -e "s|^Terminal=.*|Terminal=$TERMINAL|" \
    "$DIR/comunitat-del-anell.desktop" > "$FITXER"
chmod +x "$FITXER"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" >/dev/null 2>&1 || true
echo "Fet: La Comunitat ja és al menú d'aplicacions."

if [ "$WEBKIT" = false ]; then
  echo
  echo "Avís: falten GTK i WebKitGTK, i sense ells La Comunitat no es pot obrir en una finestra pròpia."
  if [ "$TERMINAL" = true ]; then
    echo "Tampoc hi ha Tk: funcionarà en un terminal, amb l'app al navegador."
  else
    echo "S'obrirà la finestreta de l'adreça i l'app al navegador."
  fi
  echo "Per a tindre la finestra pròpia, instal·la'ls i torna a executar ./installa.sh:"
  echo "  Debian, Ubuntu:  sudo apt install python3-gi gir1.2-webkit2-4.1"
  echo "  Fedora:          sudo dnf install python3-gobject webkit2gtk4.1"
  echo "  Arch, Manjaro:   sudo pacman -S python-gobject webkit2gtk-4.1"
  echo "  openSUSE:        sudo zypper install python3-gobject typelib-1_0-WebKit2-4_1"
fi
