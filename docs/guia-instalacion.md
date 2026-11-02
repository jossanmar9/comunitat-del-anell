# Guía de instalación

Cómo instalar La Comunidad en Windows, en Linux o en Android, o cómo usarla en el navegador sin instalar nada. Una persona lleva la partida: solo hace falta instalarla en el dispositivo que vayas a usar.

Todo se descarga de la página de [descargas](https://github.com/jossanmar9/comunitat-del-anell/releases/latest). La app web está en <https://jossanmar9.github.io/comunitat-del-anell/app/>.

## Qué hace falta

- **Windows 10 u 11** de 64 bits, **Linux** con escritorio (Ubuntu, Debian, Linux Mint, Fedora, Arch…), **Android 5.1** o posterior, o un navegador actual (Chrome, Edge, Firefox, Safari).
- Unos 50 MB de disco.
- No hace falta Internet para jugar.
- El juego de mesa «El Señor de los Anillos: El Destino de la Comunidad». La app solo lleva las cuentas.

## Windows

Hay dos versiones; elige una.

**Instalador (recomendado):** `LaComunitat-installador.exe`

1. Descárgalo y ábrelo. No pide permisos de administrador.
2. Windows SmartScreen puede avisar de que es un programa de un editor desconocido, porque no está firmado digitalmente. Pulsa **Más información → Ejecutar de todas formas**.
3. Sigue los pasos. Se crea el acceso en el menú Inicio y, si quieres, en el escritorio.

La Comunidad se abre en una ventana propia gracias a **WebView2**, el componente de Microsoft que traen Windows 11 y Windows 10 actualizado. Si en un ordenador no está, se abre la app en el navegador; para tener la ventana, instala «Microsoft Edge WebView2 Runtime» desde la web de Microsoft.

**Portable:** `LaComunitat-windows-portable.zip`

1. Descomprímelo donde quieras, también en un pendrive.
2. Abre `LaComunitat.exe` desde dentro de la carpeta.

En la versión portable, las partidas se guardan dentro de la misma carpeta, así que te la puedes llevar con todos los datos.

**Actualizar:** con La Comunidad cerrada, ejecuta el instalador de la versión nueva. Las partidas se conservan.

**Desinstalar:** desde *Configuración → Aplicaciones*. Las partidas no se borran.

## Linux

### Ubuntu, Debian, Linux Mint y similares: el paquete .deb

1. Descarga `comunitat-del-anell.deb`.
2. Haz doble clic para abrirlo con el instalador de software y pulsa **Instalar**. Desde el terminal también se puede hacer:

```
sudo apt install ./comunitat-del-anell.deb
```

3. Abre **La Comunidad** desde el menú de aplicaciones (en la sección de juegos).

El paquete instala también lo que necesita (Python 3, GTK y WebKitGTK, para la ventana propia) y la orden `comunitat-del-anell` para arrancarla desde el terminal.

**Actualizar:** instala el `.deb` de la versión nueva. **Desinstalar:** `sudo apt remove comunitat-del-anell`. Las partidas no se borran.

### Otras distribuciones: el .tar.gz

1. Comprueba que tienes Python 3 y, para la ventana propia, GTK y WebKitGTK. Casi todas las distribuciones traen Python. Sin WebKitGTK, La Comunidad se abre en el navegador con una ventanita para cerrarla (que necesita Tk); y sin ninguna de las dos, se detiene desde el terminal.

| Distribución | Orden para la ventana propia | Orden para Tk |
|---|---|---|
| Debian, Ubuntu | `sudo apt install python3-gi gir1.2-webkit2-4.1` | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-gobject webkit2gtk4.1` | `sudo dnf install python3-tkinter` |
| Arch, Manjaro | `sudo pacman -S python-gobject webkit2gtk-4.1` | `sudo pacman -S tk` |
| openSUSE | `sudo zypper install python3-gobject typelib-1_0-WebKit2-4_1` | `sudo zypper install python3-tk` |

2. Descarga `LaComunitat-linux.tar.gz` y descomprímelo donde quieras:

```
tar xzf LaComunitat-linux.tar.gz
cd LaComunitat-linux
./comunitat-del-anell.sh
```

3. Si quieres el acceso en el menú de aplicaciones, ejecuta una vez `./installa.sh`. Para quitarlo: `./installa.sh --desinstalla`.

Como en la versión portable de Windows, las partidas se guardan dentro de esa carpeta.

## Android

**El APK:** `LaComunitat-android.apk`

1. Descárgalo desde el móvil o la tableta (o pásaselo desde el ordenador).
2. Ábrelo. Android avisa de que es una app de fuera de Google Play: permite que el navegador o el gestor de archivos instalen apps («Instalar aplicaciones desconocidas») y vuelve a intentarlo.
3. Pulsa **Instalar** y abre **La Comunidad**.

Las partidas se guardan dentro de la app. **Actualizar:** instala el APK de la versión nueva encima de la antigua; las partidas se conservan. Si desinstalas la app, se borran: exporta antes las que quieras guardar.

> Google quiere que, a partir de 2027, las apps de Android que se instalan desde fuera de Google Play sean de un desarrollador verificado. Si llega el momento y tu móvil no deja instalar el APK, usa la app web: es la misma.

## En el navegador (también en el móvil, el iPhone y el iPad)

Abre <https://jossanmar9.github.io/comunitat-del-anell/app/>. No hace falta instalar nada y, después de la primera vez, funciona también sin conexión.

Para tenerla como una app más, añádela a la pantalla de inicio: en Chrome y Edge, menú **⋮ → Instalar aplicación** o **Añadir a pantalla de inicio**; en Safari, **Compartir → Añadir a pantalla de inicio**.

Las partidas se guardan en este navegador y en este dispositivo. Si borras los datos del navegador (o en modo privado, al cerrarlo), se pierden: exporta las que quieras guardar.

## Mac y otros sistemas

Además de la app web, en un Mac funciona el programa de escritorio con Python 3.8 o más nuevo. Descarga `comunitat.py` del [repositorio](https://github.com/jossanmar9/comunitat-del-anell) y, en el terminal:

```
python3 comunitat.py
```

## Dónde se guardan los datos

| Cómo está instalada | Carpeta |
|---|---|
| Windows, con el instalador | `%APPDATA%\LaComunitat` |
| Linux, con el `.deb` | `~/.local/share/comunitat-del-anell` |
| Windows portable, `.tar.gz` o `python3 comunitat.py` | La misma carpeta del programa |

Dentro están la carpeta `partides` (una partida en cada archivo), la carpeta `copies` (las copias de seguridad automáticas), `historial.json` (las partidas terminadas), `comunitat.json` (qué partida estaba abierta) y `mapa.json` (tu mapa, si pones uno). El botón **Abrir la carpeta de datos** de la pestaña Partidas la abre directamente.

Para hacer una copia de seguridad, cierra La Comunidad y copia esa carpeta entera. Si quieres guardar los datos en otro sitio (por ejemplo, una carpeta sincronizada con la nube), arranca con `--dades CARPETA`.

### Actualizar desde la versión 2

La versión 3 lee las mismas carpetas y archivos. La primera vez que se abre, si la 2.7 había dejado cambios en `comunitat.sqlite3`, los pasa a los archivos de siempre y guarda la base de datos en `copies/v2/`. Los jugadores, los PIN y las sesiones de la sala ya no se usan.

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
| `--dades CARPETA` | Guarda los datos en esa carpeta (por ejemplo, una carpeta sincronizada con la nube). |
| `--navegador` | Abre la app en el navegador, con una ventanita para cerrarla, en lugar de la ventana propia. |
| `--sense-finestra` | No abre ninguna ventana: la dirección sale en el terminal y se detiene con Ctrl+C. |
| `--sense-navegador` | Con `--navegador`, no abre el navegador al arrancar. |
| `--port 9001` | Usa otro puerto local (el normal es el 8766; si está ocupado, se elige otro). |
| `--idioma es` | Los avisos de las ventanas en castellano. Por defecto, en valenciano (`ca`). |

La Comunidad solo acepta conexiones del mismo ordenador: desde otros dispositivos no se puede entrar.

## Si algo no funciona

| Qué pasa | Qué hacer |
|---|---|
| Windows no deja abrir el programa | Es el aviso de SmartScreen: **Más información → Ejecutar de todas formas**. |
| Android no deja instalar el APK | Permite «Instalar aplicaciones desconocidas» en la app desde la que lo abres (el navegador o Archivos). Si aun así no se puede, usa la app web. |
| Android dice que la app no se ha instalado al actualizar | El APK nuevo tiene que estar firmado con la misma clave que el antiguo. Si lo has descargado de otro sitio, descárgalo de la página de descargas. |
| Se abre el navegador en lugar de la ventana propia | En Windows, falta WebView2 (ver más arriba). En Linux, faltan GTK y WebKitGTK: instálalos con la orden de tu distribución. |
| En Linux no se abre ninguna ventana | Faltan WebKitGTK y Tk: instala al menos uno. Mientras tanto, la dirección sale en el terminal. |
| «La Comunidad ya está abierta» | Ya hay otra Comunidad abierta con la misma carpeta de datos: búscala en la barra de tareas. |

Para todo lo que se puede hacer con la app, consulta el [manual de usuario](manual-usuario.md).
