# Guia d'instal·lació

Com instal·lar La Comunitat a Windows, a Linux o a Android, o com fer-la servir al navegador sense instal·lar res. Una persona porta la partida: només cal instal·lar-la a l'aparell que faràs servir.

Tot es baixa de la pàgina de [descàrregues](https://github.com/jossanmar9/comunitat-del-anell/releases/latest). L'app web és a <https://jossanmar9.github.io/comunitat-del-anell/app/>.

## Què cal

- **Windows 10 o 11** de 64 bits, **Linux** amb escriptori (Ubuntu, Debian, Linux Mint, Fedora, Arch…), **Android 5.1** o més nou, o un navegador actual (Chrome, Edge, Firefox, Safari).
- Uns 50 MB de disc.
- No cal Internet per a jugar.
- El joc de taula «El Señor de los Anillos: El Destino de la Comunidad». L'app només porta els comptes.

## Windows

Hi ha dues versions; tria'n una.

**Instal·lador (recomanat):** `LaComunitat-installador.exe`

1. Baixa'l i obri'l. No demana permisos d'administrador.
2. Windows SmartScreen pot avisar que és un programa d'un editor desconegut, perquè no està signat digitalment. Prem **Més informació → Executa igualment**.
3. Segueix els passos. Es crea l'accés al menú Inici i, si vols, a l'escriptori.

La Comunitat s'obri en una finestra pròpia gràcies a **WebView2**, el component de Microsoft que porten Windows 11 i Windows 10 actualitzat. Si en un ordinador no hi és, s'obri l'app al navegador; per a tindre la finestra, instal·la «Microsoft Edge WebView2 Runtime» des de la web de Microsoft.

**Portable:** `LaComunitat-windows-portable.zip`

1. Descomprimeix-lo on vulgues, també en una memòria USB.
2. Obri `LaComunitat.exe` de dins de la carpeta.

En la versió portable, les partides es guarden dins de la mateixa carpeta, així que pots portar-te-la amb totes les dades.

**Actualitzar:** amb La Comunitat tancada, executa l'instal·lador de la versió nova. Les partides es conserven.

**Desinstal·lar:** des de *Configuració → Aplicacions*. Les partides no s'esborren.

## Linux

### Ubuntu, Debian, Linux Mint i semblants: el paquet .deb

1. Baixa `comunitat-del-anell.deb`.
2. Fes-hi doble clic per a obrir-lo amb l'instal·lador de programari i prem **Instal·la**. Des del terminal també es pot fer:

```
sudo apt install ./comunitat-del-anell.deb
```

3. Obri **La Comunitat** des del menú d'aplicacions (a la secció de jocs).

El paquet instal·la també el que necessita (Python 3, GTK i WebKitGTK, per a la finestra pròpia) i l'ordre `comunitat-del-anell` per a arrancar-la des del terminal.

**Actualitzar:** instal·la el `.deb` de la versió nova. **Desinstal·lar:** `sudo apt remove comunitat-del-anell`. Les partides no s'esborren.

### Altres distribucions: el .tar.gz

1. Comprova que tens Python 3 i, per a la finestra pròpia, GTK i WebKitGTK. Quasi totes les distribucions porten Python. Sense WebKitGTK, La Comunitat s'obri al navegador amb una finestreta per a tancar-la (que necessita Tk); i sense cap de les dues, s'atura des del terminal.

| Distribució | Ordre per a la finestra pròpia | Ordre per a Tk |
|---|---|---|
| Debian, Ubuntu | `sudo apt install python3-gi gir1.2-webkit2-4.1` | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-gobject webkit2gtk4.1` | `sudo dnf install python3-tkinter` |
| Arch, Manjaro | `sudo pacman -S python-gobject webkit2gtk-4.1` | `sudo pacman -S tk` |
| openSUSE | `sudo zypper install python3-gobject typelib-1_0-WebKit2-4_1` | `sudo zypper install python3-tk` |

2. Baixa `LaComunitat-linux.tar.gz` i descomprimeix-lo on vulgues:

```
tar xzf LaComunitat-linux.tar.gz
cd LaComunitat-linux
./comunitat-del-anell.sh
```

3. Si vols l'accés al menú d'aplicacions, executa una vegada `./installa.sh`. Per a llevar-lo: `./installa.sh --desinstalla`.

Com en la versió portable de Windows, les partides es guarden dins d'eixa carpeta.

## Android

**L'APK:** `LaComunitat-android.apk`

1. Baixa'l des del mòbil o la tauleta (o passa-l'hi des de l'ordinador).
2. Obri'l. Android avisa que és una app de fora de Google Play: permet que el navegador o el gestor de fitxers instal·len apps («Instal·lar apps desconegudes») i torna-ho a provar.
3. Prem **Instal·la** i obri **La Comunitat**.

Les partides es guarden dins de l'app. **Actualitzar:** instal·la l'APK de la versió nova damunt de l'antiga; les partides es conserven. Si desinstal·les l'app, s'esborren: exporta abans les que vulgues guardar.

> Google vol que, a partir del 2027, les apps d'Android que s'instal·len de fora de Google Play siguen d'un desenvolupador verificat. Si arriba el moment i el teu mòbil no deixa instal·lar l'APK, fes servir l'app web: és la mateixa.

## Al navegador (també al mòbil, a l'iPhone i a l'iPad)

Obri <https://jossanmar9.github.io/comunitat-del-anell/app/>. No cal instal·lar res i, després de la primera vegada, funciona també sense connexió.

Per a tindre-la com una app més, afig-la a la pantalla d'inici: a Chrome i Edge, menú **⋮ → Instal·lar l'aplicació** o **Afegir a la pantalla d'inici**; a Safari, **Compartir → Afegir a la pantalla d'inici**.

Les partides es guarden en aquest navegador i en aquest aparell. Si esborres les dades del navegador (o en mode privat, en tancar-lo), es perden: exporta les que vulgues guardar.

## Mac i altres sistemes

A més de l'app web, en un Mac funciona el programa d'escriptori amb Python 3.8 o més nou. Baixa `comunitat.py` del [repositori](https://github.com/jossanmar9/comunitat-del-anell) i, al terminal:

```
python3 comunitat.py
```

## On es guarden les dades

| Com està instal·lada | Carpeta |
|---|---|
| Windows, amb l'instal·lador | `%APPDATA%\LaComunitat` |
| Linux, amb el `.deb` | `~/.local/share/comunitat-del-anell` |
| Windows portable, `.tar.gz` o `python3 comunitat.py` | La mateixa carpeta del programa |

Dins hi ha la carpeta `partides` (una partida en cada fitxer), la carpeta `copies` (les còpies de seguretat automàtiques), `historial.json` (les partides acabades), `comunitat.json` (quina partida estava oberta) i `mapa.json` (el teu mapa, si en poses un). El botó **Obrir la carpeta de dades** de la pestanya Partides l'obri directament.

Per a fer una còpia de seguretat, tanca La Comunitat i copia eixa carpeta sencera. Si vols guardar les dades en un altre lloc (per exemple, una carpeta sincronitzada amb el núvol), arranca amb `--dades CARPETA`.

### Actualitzar des de la versió 2

La versió 3 llig les mateixes carpetes i fitxers. La primera vegada que s'obri, si la 2.7 havia deixat canvis a `comunitat.sqlite3`, els passa als fitxers de sempre i guarda la base de dades a `copies/v2/`. Els jugadors, els PIN i les sessions de la sala ja no es fan servir.

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
| `--dades CARPETA` | Guarda les dades en eixa carpeta (per exemple, una carpeta sincronitzada amb el núvol). |
| `--navegador` | Obri l'app al navegador, amb una finestreta per a tancar-la, en compte de la finestra pròpia. |
| `--sense-finestra` | No obri cap finestra: l'adreça ix al terminal i s'atura amb Ctrl+C. |
| `--sense-navegador` | Amb `--navegador`, no obri el navegador en arrancar. |
| `--port 9001` | Fa servir un altre port local (el normal és el 8766; si està ocupat, se'n tria un altre). |
| `--idioma es` | Els avisos de les finestres en castellà. Per defecte, en valencià (`ca`). |

La Comunitat només accepta connexions del mateix ordinador: des d'altres aparells no s'hi pot entrar.

## Si alguna cosa no va

| Què passa | Què fer |
|---|---|
| Windows no deixa obrir el programa | És l'avís de SmartScreen: **Més informació → Executa igualment**. |
| Android no deixa instal·lar l'APK | Permet «Instal·lar apps desconegudes» a l'app des d'on l'obris (el navegador o Fitxers). Si tot i així no es pot, fes servir l'app web. |
| Android diu que l'app no s'ha instal·lat en actualitzar | L'APK nou s'ha de signar amb la mateixa clau que l'antic. Si l'has baixat d'un altre lloc, baixa'l de la pàgina de descàrregues. |
| S'obri el navegador en compte de la finestra pròpia | A Windows, falta WebView2 (vegeu més amunt). A Linux, falten GTK i WebKitGTK: instal·la'ls amb l'ordre de la teua distribució. |
| A Linux no s'obri cap finestra | Falten WebKitGTK i Tk: instal·la'n almenys un. Mentrestant, l'adreça ix al terminal. |
| «La Comunitat ja està oberta» | Ja hi ha una altra Comunitat oberta amb la mateixa carpeta de dades: busca-la a la barra de tasques. |

Per a tot el que es pot fer amb l'app, consulta el [manual d'usuari](manual-usuari.md).
