# Guía de instalación

Cómo instalar La Comunidad del Anillo en el ordenador que hará de servidor, en Windows o en Linux. Los jugadores no tienen que instalar nada: solo necesitan un navegador y la misma wifi.

Todo se descarga de la página de [descargas](https://github.com/jossanmar9/comunitat-del-anell/releases/latest).

## Qué hace falta

- **Windows 10 u 11** de 64 bits, o **Linux** con escritorio (Ubuntu, Debian, Linux Mint, Fedora, Arch…).
- Unos 50 MB de disco.
- El ordenador y los dispositivos de los jugadores, en la **misma wifi**. No hace falta Internet.
- El juego de mesa «El Señor de los Anillos: El Destino de la Comunidad». La app solo lleva las cuentas.

## Windows

Hay dos versiones; elige una.

**Instalador (recomendado):** `LaComunitat-X.Y-installador.exe`

1. Descárgalo y ábrelo. No pide permisos de administrador.
2. Windows SmartScreen puede avisar de que es un programa de un editor desconocido, porque no está firmado digitalmente. Pulsa **Más información → Ejecutar de todas formas**.
3. Sigue los pasos. Se crea el acceso en el menú Inicio y, si quieres, en el escritorio.

**Portable:** `LaComunitat-X.Y-windows-portable.zip`

1. Descomprímelo donde quieras, también en un pendrive.
2. Abre `LaComunitat.exe` desde dentro de la carpeta.

En la versión portable, las partidas se guardan dentro de la misma carpeta, así que te la puedes llevar con todos los datos.

**La primera vez**, Windows pregunta si el programa puede usar la red. Marca **Redes privadas** y pulsa **Permitir acceso**. Si no lo haces, los jugadores no podrán entrar. Comprueba también que la wifi de casa está configurada como red privada.

**Actualizar:** con La Comunidad cerrada, ejecuta el instalador de la versión nueva. Las partidas se conservan.

**Desinstalar:** desde *Configuración → Aplicaciones*. Las partidas no se borran.

## Linux

### Ubuntu, Debian, Linux Mint y similares: el paquete .deb

1. Descarga `comunitat-del-anell_X.Y_all.deb`.
2. Haz doble clic para abrirlo con el instalador de software y pulsa **Instalar**. Desde el terminal también se puede hacer:

```
sudo apt install ./comunitat-del-anell_X.Y_all.deb
```

3. Abre **La Comunidad del Anillo** desde el menú de aplicaciones (en la sección de juegos).

El paquete instala también lo que necesita (Python 3 y Tk) y la orden `comunitat-del-anell` para arrancarla desde el terminal.

**Actualizar:** instala el `.deb` de la versión nueva. **Desinstalar:** `sudo apt remove comunitat-del-anell`. Las partidas no se borran.

### Otras distribuciones: el .tar.gz

1. Comprueba que tienes Python 3 y Tk. Casi todas las distribuciones traen Python; si no tienes Tk, La Comunidad funciona igual pero sin la ventana, solo en el terminal.

| Distribución | Orden para instalar Tk |
|---|---|
| Fedora | `sudo dnf install python3-tkinter` |
| Arch, Manjaro | `sudo pacman -S tk` |
| openSUSE | `sudo zypper install python3-tk` |
| Debian, Ubuntu | `sudo apt install python3-tk` |

2. Descarga `LaComunitat-X.Y-linux.tar.gz` y descomprímelo donde quieras:

```
tar xzf LaComunitat-X.Y-linux.tar.gz
cd LaComunitat-X.Y-linux
./comunitat-del-anell.sh
```

3. Si quieres el acceso en el menú de aplicaciones, ejecuta una vez `./installa.sh`. Para quitarlo: `./installa.sh --desinstalla`.

Como en la versión portable de Windows, las partidas se guardan dentro de esa carpeta.

**Cortafuegos:** si tienes uno (por ejemplo `ufw`), abre el puerto para que entren los jugadores: `sudo ufw allow 8766/tcp`.

## Mac y otros sistemas

No hay paquete para Mac, pero funciona con Python 3.8 o más nuevo. Descarga `comunitat.py` del [repositorio](https://github.com/jossanmar9/comunitat-del-anell) y, en el terminal:

```
python3 comunitat.py
```

## Dónde se guardan los datos

| Cómo está instalada | Carpeta |
|---|---|
| Windows, con el instalador | `%APPDATA%\LaComunitat` |
| Linux, con el `.deb` | `~/.local/share/comunitat-del-anell` |
| Windows portable, `.tar.gz` o `python3 comunitat.py` | La misma carpeta del programa |

Dentro están la carpeta `partides` (una partida en cada archivo), el archivo `comunitat.json` (los jugadores) e `historial.json` (las partidas terminadas). Aquí va también tu mapa, si pones uno (`mapa.jpg`). El botón **Carpeta de datos** de la ventana la abre directamente.

Para hacer una copia de seguridad, copia esa carpeta entera. Si quieres guardar los datos en otro sitio (por ejemplo, una carpeta sincronizada con la nube), arranca con `--dades CARPETA`.

### Pasar las partidas de la versión 1.x

Las versiones 1.x guardaban las partidas junto a `LaComunitat.exe` o a `comunitat.py`. Si ahora usas el instalador o el `.deb`:

1. Cierra La Comunidad.
2. Copia la carpeta `partides` y los archivos `comunitat.json` e `historial.json` (y tu `mapa.jpg`, si tenías uno) de la carpeta antigua a la carpeta nueva de la tabla anterior.
3. Vuelve a abrir La Comunidad.

Si sigues con la versión portable, solo tienes que copiarlos a la carpeta nueva.

## Opciones

La Comunidad acepta estas opciones al arrancarla desde el terminal (`comunitat-del-anell` con el `.deb`, `./comunitat-del-anell.sh` con el `.tar.gz`, `LaComunitat.exe` en Windows o `python3 comunitat.py`). Los nombres de las opciones están en valenciano:

| Opción | Qué hace |
|---|---|
| `--port 9001` | Usa otro puerto (el normal es el 8766). |
| `--partida "Viernes"` | Abre esa partida al arrancar (la crea si no existe). |
| `--dades CARPETA` | Guarda los datos en esa carpeta. |
| `--sense-finestra` | No abre la ventana: todo va al terminal, con el QR. Útil en un ordenador sin pantalla. |
| `--sense-navegador` | No abre el navegador al arrancar. |
| `--sense-qr` | No muestra el QR en el terminal. |
| `--idioma es` | Muestra la ventana en castellano (`ca` para valenciano). Por defecto, el del sistema. |

## Si algo no funciona

| Qué pasa | Qué hacer |
|---|---|
| Windows no deja abrir el programa | Es el aviso de SmartScreen: **Más información → Ejecutar de todas formas**. |
| Los demás no pueden entrar | Misma wifi, red privada y el programa permitido en el cortafuegos (ver más arriba). |
| En Linux no se abre la ventana | Falta Tk: instálalo con la orden de tu distribución. Mientras tanto, la información sale en el terminal. |
| «El puerto ya está en uso» | Ya hay otra Comunidad abierta. Ciérrala o arranca con `--port 9001`. |

Para todo lo que se puede hacer con la app, consulta el [manual de usuario](manual-usuario.md).
