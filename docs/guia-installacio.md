# Guia d'instal·lació

Com instal·lar La Comunitat a l'ordinador que farà de servidor, a Windows o a Linux. Els jugadors no han d'instal·lar res: només necessiten un navegador i la mateixa wifi.

Tot es baixa de la pàgina de [descàrregues](https://github.com/jossanmar9/comunitat-del-anell/releases/latest).

## Què cal

- **Windows 10 o 11** de 64 bits, o **Linux** amb escriptori (Ubuntu, Debian, Linux Mint, Fedora, Arch…).
- Uns 50 MB de disc.
- L'ordinador i els dispositius dels jugadors, a la **mateixa wifi**. No cal Internet.
- El joc de taula «El Señor de los Anillos: El Destino de la Comunidad». L'app només porta els comptes.

## Windows

Hi ha dues versions; tria'n una.

**Instal·lador (recomanat):** `LaComunitat-X.Y-installador.exe`

1. Baixa'l i obri'l. No demana permisos d'administrador.
2. Windows SmartScreen pot avisar que és un programa d'un editor desconegut, perquè no està signat digitalment. Prem **Més informació → Executa igualment**.
3. Segueix els passos. Es crea l'accés al menú Inici i, si vols, a l'escriptori.

La Comunitat s'obri en una finestra pròpia gràcies a **WebView2**, el component de Microsoft que porten Windows 11 i Windows 10 actualitzat. Si en un ordinador no hi és, s'obri l'app al navegador; per a tindre la finestra, instal·la «Microsoft Edge WebView2 Runtime» des de la web de Microsoft.

**Portable:** `LaComunitat-X.Y-windows-portable.zip`

1. Descomprimeix-lo on vulgues, també en una memòria USB.
2. Obri `LaComunitat.exe` de dins de la carpeta.

En la versió portable, les partides es guarden dins de la mateixa carpeta, així que pots portar-te-la amb totes les dades.

**La primera vegada**, Windows demana si el programa pot fer servir la xarxa. Marca **Xarxes privades** i prem **Permet l'accés**. Si no ho fas, els jugadors no podran entrar. Comprova també que la wifi de casa està configurada com a xarxa privada.

**Actualitzar:** amb La Comunitat tancada, executa l'instal·lador de la versió nova. Les partides es conserven.

**Desinstal·lar:** des de *Configuració → Aplicacions*. Les partides no s'esborren.

## Linux

### Ubuntu, Debian, Linux Mint i semblants: el paquet .deb

1. Baixa `comunitat-del-anell_X.Y_all.deb`.
2. Fes-hi doble clic per a obrir-lo amb l'instal·lador de programari i prem **Instal·la**. Des del terminal també es pot fer:

```
sudo apt install ./comunitat-del-anell_X.Y_all.deb
```

3. Obri **La Comunitat** des del menú d'aplicacions (a la secció de jocs).

El paquet instal·la també el que necessita (Python 3, GTK i WebKitGTK, per a la finestra pròpia) i l'ordre `comunitat-del-anell` per a arrancar-la des del terminal.

**Actualitzar:** instal·la el `.deb` de la versió nova. **Desinstal·lar:** `sudo apt remove comunitat-del-anell`. Les partides no s'esborren.

### Altres distribucions: el .tar.gz

1. Comprova que tens Python 3 i, per a la finestra pròpia, GTK i WebKitGTK. Quasi totes les distribucions porten Python. Sense WebKitGTK, La Comunitat s'obri al navegador amb una finestreta per al QR (que necessita Tk); i sense cap de les dues, funciona al terminal.

| Distribució | Ordre per a la finestra pròpia | Ordre per a Tk |
|---|---|---|
| Debian, Ubuntu | `sudo apt install python3-gi gir1.2-webkit2-4.1` | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-gobject webkit2gtk4.1` | `sudo dnf install python3-tkinter` |
| Arch, Manjaro | `sudo pacman -S python-gobject webkit2gtk-4.1` | `sudo pacman -S tk` |
| openSUSE | `sudo zypper install python3-gobject typelib-1_0-WebKit2-4_1` | `sudo zypper install python3-tk` |

2. Baixa `LaComunitat-X.Y-linux.tar.gz` i descomprimeix-lo on vulgues:

```
tar xzf LaComunitat-X.Y-linux.tar.gz
cd LaComunitat-X.Y-linux
./comunitat-del-anell.sh
```

3. Si vols l'accés al menú d'aplicacions, executa una vegada `./installa.sh`. Per a llevar-lo: `./installa.sh --desinstalla`.

Com en la versió portable de Windows, les partides es guarden dins d'eixa carpeta.

**Tallafoc:** si en tens (per exemple `ufw`), obri el port perquè entren els jugadors: `sudo ufw allow 8766/tcp`.

## Mac i altres sistemes

No hi ha paquet per a Mac, però funciona amb Python 3.8 o més nou. Baixa `comunitat.py` del [repositori](https://github.com/jossanmar9/comunitat-del-anell) i, al terminal:

```
python3 comunitat.py
```

## On es guarden les dades

| Com està instal·lada | Carpeta |
|---|---|
| Windows, amb l'instal·lador | `%APPDATA%\LaComunitat` |
| Linux, amb el `.deb` | `~/.local/share/comunitat-del-anell` |
| Windows portable, `.tar.gz` o `python3 comunitat.py` | La mateixa carpeta del programa |

Dins hi ha la carpeta `partides` (una partida en cada fitxer), la carpeta `copies` (les còpies de seguretat automàtiques), el fitxer `comunitat.json` (els jugadors) i `historial.json` (les partides acabades). Ací també va el teu mapa, si en poses un (`mapa.jpg`). El botó **Obrir la carpeta de dades** de la pestanya Partides l'obri directament.

Per a fer una còpia de seguretat, copia eixa carpeta sencera. Si vols guardar les dades en un altre lloc (per exemple, una carpeta sincronitzada amb el núvol), arranca amb `--dades CARPETA`.

### Passar les partides de la versió 1.x

Les versions 1.x guardaven les partides al costat de `LaComunitat.exe` o de `comunitat.py`. Si ara fas servir l'instal·lador o el `.deb`:

1. Tanca La Comunitat.
2. Copia la carpeta `partides` i els fitxers `comunitat.json` i `historial.json` (i el teu `mapa.jpg`, si en tenies) de la carpeta antiga a la carpeta nova de la taula d'abans.
3. Torna a obrir La Comunitat.

Si continues amb la versió portable, només cal que els copies a la carpeta nova.

## Opcions

La Comunitat accepta aquestes opcions en arrancar-la des del terminal (`comunitat-del-anell` amb el `.deb`, `./comunitat-del-anell.sh` amb el `.tar.gz`, `LaComunitat.exe` a Windows o `python3 comunitat.py`):

| Opció | Què fa |
|---|---|
| `--port 9001` | Fa servir un altre port (el normal és el 8766). |
| `--partida "Divendres"` | Obri eixa partida en arrancar (la crea si no existeix). |
| `--dades CARPETA` | Guarda les dades en eixa carpeta. |
| `--navegador` | Obri l'app al navegador, amb la finestreta de l'adreça i el QR, en compte de la finestra pròpia. |
| `--sense-finestra` | No obri cap finestra: tot va al terminal, amb el QR. Útil en un ordinador sense pantalla. |
| `--sense-navegador` | Amb `--navegador`, no obri el navegador en arrancar. |
| `--sense-qr` | No mostra el QR al terminal. |
| `--idioma es` | Els avisos de les finestres en castellà. Per defecte, en valencià (`ca`). |

## Si alguna cosa no va

| Què passa | Què fer |
|---|---|
| Windows no deixa obrir el programa | És l'avís de SmartScreen: **Més informació → Executa igualment**. |
| Els altres no hi poden entrar | Mateixa wifi, xarxa privada i el programa permés al tallafoc (vegeu més amunt). |
| S'obri el navegador en compte de la finestra pròpia | A Windows, falta WebView2 (vegeu més amunt). A Linux, falten GTK i WebKitGTK: instal·la'ls amb l'ordre de la teua distribució. |
| A Linux no s'obri cap finestra | Falten WebKitGTK i Tk: instal·la'n almenys un. Mentrestant, la informació ix al terminal. |
| «El port ja està en ús» | Ja hi ha una altra Comunitat oberta. Tanca-la o arranca amb `--port 9001`. |

Per a tot el que es pot fer amb l'app, consulta el [manual d'usuari](manual-usuari.md).
