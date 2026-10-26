<p align="center"><img src="logo.png" alt="La Comunidad" width="220"></p>

<p align="center">
  <a href="../../releases/latest"><img src="https://img.shields.io/github/v/release/jossanmar9/comunitat-del-anell?label=versi%C3%B3n&color=8C2A1C" alt="Última versión"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/licencia-GPL--3.0--or--later-2A1C10" alt="Licencia GPL-3.0-or-later"></a>
  <img src="https://img.shields.io/badge/Windows-10%20%7C%2011-A27419" alt="Windows 10 y 11">
  <img src="https://img.shields.io/badge/Linux-.deb%20%7C%20.tar.gz-A27419" alt="Linux">
  <a href="../../actions/workflows/proves.yml"><img src="https://github.com/jossanmar9/comunitat-del-anell/actions/workflows/proves.yml/badge.svg" alt="Pruebas"></a>
</p>

[Valencià](README.md) · **Castellano**

# La Comunidad

**Ayudante libre para llevar las partidas de «El Señor de los Anillos: El Destino de la Comunidad».** El tablero y las piezas los tenéis en la mesa; la app lleva las cuentas: la Esperanza, la Amenaza, el turno paso a paso, cuántos dados tirar en cada tirada y qué se pierde con el resultado. Un ordenador hace de servidor y el resto de la mesa entra desde el navegador, móviles incluidos. En castellano y valenciano, y sin Internet.

Funciona en **Windows y Linux**. Se instala como cualquier otro programa y, en el ordenador principal, se abre en **una ventana propia**, sin navegador. Las partidas se quedan en el ordenador de casa y no se conecta a ningún servidor de fuera.

🌐 **Web:** [jossanmar9.github.io/comunitat-del-anell](https://jossanmar9.github.io/comunitat-del-anell/es/) · 🎲 **Pruébala:** [en el navegador](https://jossanmar9.github.io/comunitat-del-anell/prova/) · ⬇️ **Descarga:** [última versión](../../releases/latest) · 📖 **Manual:** [en línea](docs/manual-usuario.md) y en PDF en cada versión

![La pantalla de juego: las herramientas, el mapa y el turno paso a paso](docs/imatges/es/05-partida.jpg)

## Contenido

- [Qué hace](#qué-hace)
- [Capturas](#capturas)
- [Instalación](#instalación)
- [Primeros pasos](#primeros-pasos)
- [Datos y copias de seguridad](#datos-y-copias-de-seguridad)
- [Documentación](#documentación)
- [Para desarrollar](#para-desarrollar)
- [Publicar una versión](#publicar-una-versión)
- [Colaborar](#colaborar)
- [Uso de inteligencia artificial](#uso-de-inteligencia-artificial)
- [Licencia](#licencia)

## Qué hace

| Sección | Qué hace |
|---|---|
| **Marcadores** | Esperanza (de 0 a 8), nivel de Amenaza (cuántas cartas de Sombra se roban), cartas «El cielo se oscurece» salidas, cartas que quedan en el mazo, objetivos completados y ronda. Se corrigen a mano y todo se puede **deshacer** hasta 30 pasos. |
| **El turno paso a paso** | Las 4 + 1 acciones, robar 2 cartas (descuenta el mazo y resta Esperanza si se acaba) y resolver las cartas de Sombra que tocan, en el orden del reglamento. |
| **Tiradas de búsqueda** | Cuántos dados tirar según los Nazgûl y las Tropas de la Sombra, y qué se pierde con el resultado. Tiene en cuenta los Refugios, Mordor y ponerse el Anillo. |
| **Batallas** | Ataque de un personaje o provocada por la Sombra: cuántos dados, la Heroicidad gastada y cuántas Tropas hay que quitar de cada bando. Avisa si se pierde un Refugio. |
| **Cartas especiales** | *El cielo se oscurece* con sus cuatro pasos («¡Te veo!» incluido), la carta de Sombra y destruir el Anillo Único. |
| **Preparación** | Cinco niveles de dificultad, escenarios sugeridos, los 24 objetivos, los 13 personajes con retrato y la lista de preparación del tablero, paso a paso. |
| **Resumen e historial** | Al terminar, dónde se ha perdido la Esperanza, rondas, duración y tiradas. El historial guarda todas las partidas terminadas, con victorias y derrotas por dificultad. |
| **Partidas y copias** | Varias partidas guardadas, que se pueden duplicar, exportar, importar en otro ordenador y borrar (sin perderlas). **Copias de seguridad automáticas** de cada partida, para volver a un momento anterior. |

Además: un **registro** de todo lo que pasa, entrada con **QR**, **modo oscuro**, adaptada al **móvil** y un **mapa** de la Tierra Media que se puede cambiar por el tuyo. Todo el programa está en **castellano y valenciano**, y cada jugador elige su idioma.

## Capturas

| | |
|---|---|
| ![Preparación](docs/imatges/es/03-preparacio.jpg) | ![Tirada de búsqueda](docs/imatges/es/11-cerca-daus.jpg) |
| La preparación: dificultad, participantes, personajes y objetivos. | Una tirada de búsqueda: la app dice cuántos dados tirar y aplica el resultado. |
| ![Resumen de la partida](docs/imatges/es/18-resum.jpg) | ![La app en un móvil](docs/imatges/es/21-mobil.jpg) |
| El resumen al terminar la partida. | En el móvil, en una sola columna. |

<p align="center"><img src="docs/imatges/personatges.webp" alt="Los retratos de los personajes" width="640"></p>

Hay más capturas, paso a paso, en el [manual de usuario](docs/manual-usuario.md).

## Instalación

**Requisitos:** Windows 10 u 11 de 64 bits, o Linux con escritorio, y unos 50 MB de disco. Los jugadores solo necesitan un navegador y estar en la misma wifi. No hace falta Internet. Y el juego de mesa, claro: la app no incluye ningún componente del juego.

Descarga la [última versión](../../releases/latest):

| Sistema | Archivo |
|---|---|
| **Windows** (recomendado) | `LaComunitat-X.Y-installador.exe`. No pide permisos de administrador; crea el acceso en el menú Inicio y, si quieres, en el escritorio. |
| **Windows** portable | `LaComunitat-X.Y-windows-portable.zip`. Descomprímelo donde quieras (también en un pendrive) y abre `LaComunitat.exe`. |
| **Ubuntu, Debian, Linux Mint…** | `comunitat-del-anell_X.Y_all.deb`. Doble clic para instalarlo, o `sudo apt install ./comunitat-del-anell_X.Y_all.deb`. |
| **Otros Linux** | `LaComunitat-X.Y-linux.tar.gz`. Descomprímelo y abre `comunitat-del-anell.sh`; `./installa.sh` lo añade al menú. Hace falta Python 3 y, para la ventana propia, GTK y WebKitGTK. |

El programa no está firmado digitalmente: en Windows, SmartScreen puede avisar. Pulsa **Más información → Ejecutar de todas formas**. La primera vez, permítele el acceso a las **redes privadas** para que puedan entrar los jugadores.

Más detalles, el cortafuegos de Linux y cómo pasar las partidas de las versiones 1.x, en la [guía de instalación](docs/guia-instalacion.md).

**Sin instalar nada** (Linux, Mac o Windows con Python 3.8 o más nuevo): descarga [`comunitat.py`](comunitat.py) y ejecuta `python3 comunitat.py`. Para tenerla en una ventana propia, en Windows y Mac hace falta [pywebview](https://pywebview.flowrl.com/) (`pip install pywebview`) y en Linux, GTK y WebKitGTK; si no, se abre en el navegador.

## Primeros pasos

1. Abre **La Comunidad**. La app se abre en una ventana propia, sin navegador (en Windows con WebView2, en Linux con WebKitGTK). Mientras la ventana esté abierta, La Comunidad funciona; al cerrarla, lo guarda todo y se detiene.
2. El botón **Invitar** muestra la dirección para los demás y un **código QR**. Cada jugador lo escanea con el móvil y entra con su nombre. No hay contraseña: el juego es cooperativo y todo el mundo puede hacer cambios.
3. Rellenad el formulario de preparación, preparad el tablero con la lista de la pestaña **Comunidad** y a jugar.

Opciones para el terminal (los nombres de las opciones están en valenciano):

```bash
comunitat-del-anell --port 9001             # otro puerto (el normal es el 8766)
comunitat-del-anell --partida "Viernes"     # abre (o crea) esa partida
comunitat-del-anell --dades ~/Partidas      # guarda los datos en otra carpeta
comunitat-del-anell --navegador            # la app en el navegador, con la ventanita de la dirección y el QR
comunitat-del-anell --sense-finestra        # sin ventanas: todo en el terminal, con el QR
comunitat-del-anell --idioma es             # los avisos de las ventanas en castellano (por defecto, en valenciano)
```

(En Windows, `LaComunitat.exe`; con el `.tar.gz`, `./comunitat-del-anell.sh`; sin instalar, `python3 comunitat.py`.)

## Datos y copias de seguridad

| Cómo está instalada | Dónde se guardan los datos |
|---|---|
| Windows, con el instalador | `%APPDATA%\LaComunitat` |
| Linux, con el `.deb` | `~/.local/share/comunitat-del-anell` |
| Windows portable, `.tar.gz` o `python3 comunitat.py` | La carpeta del programa |

Cada partida se guarda en `partides/<nombre>.json`, sus copias de seguridad en `copies/<nombre>/`, los jugadores en `comunitat.json` y las partidas terminadas en `historial.json`. La Comunidad hace una copia de cada partida al abrirla y cada media hora mientras se juega, y guarda las 15 últimas; se restauran desde la pestaña **Partidas → Copias**. Para guardarlo todo aparte, copia la carpeta entera; el botón **Abrir la carpeta de datos** de la pestaña Partidas la abre directamente. Al desinstalar, las partidas no se borran.

**El mapa:** para poner el tuyo en lugar del de ejemplo, copia la imagen en esa carpeta con el nombre `mapa.jpg` (o `mapa.png`). Si lo tienes en los dos idiomas, llámalos `mapa-es.jpg` y `mapa-val.jpg`.

## Documentación

- [Registro de cambios](CHANGELOG.md)
| Documento | Valencià | Castellano |
|---|---|---|
| Manual de usuario | [manual-usuari.md](docs/manual-usuari.md) | [manual-usuario.md](docs/manual-usuario.md) |
| Guía de instalación | [guia-installacio.md](docs/guia-installacio.md) | [guia-instalacion.md](docs/guia-instalacion.md) |

Los PDF se generan solos a partir de estos archivos y van adjuntos a cada [versión](../../releases/latest), dentro de los paquetes y en la [web](https://jossanmar9.github.io/comunitat-del-anell/es/).

## Para desarrollar

Solo hace falta **Python 3.8 o más nuevo**, sin dependencias. `comunitat.py` se genera a partir de `src/`:

| Archivo | Qué hay |
|---|---|
| `src/servidor.py` | El servidor, el historial y dónde se guardan los datos |
| `src/finestra.py` | La ventanita con la dirección y el QR (Tk) |
| `src/qr.py` | El generador de códigos QR |
| `src/mapes/` | Los mapas de ejemplo, en valenciano y castellano, que van dentro del programa |
| `src/web/app.js` | La lógica de la página: marcadores, turno, tiradas, preparación, resumen y partidas |
| `src/web/dades.js` | Personajes, objetivos, escenarios y preparación del tablero |
| `src/web/personatges/` | Los retratos de los personajes (WebP de 200 px) |
| `src/web/i18n.js` | Las traducciones al castellano (para añadir un idioma, copia el bloque `es`) |
| `src/web/cos.html`, `estil-base.css`, `estil.css` | La estructura y el estilo de la página |
| `src/web/fonts/` | Las tipografías (Alegreya e IM Fell English, licencia OFL), que van dentro del programa |
| `tests/prova_servidor.py` | Las pruebas automáticas del servidor |
| `docs/` | Los manuales en Markdown y las capturas |
| `paquets/` | El instalador de Windows (Inno Setup) y los archivos del menú de Linux |
| `eines/` | Comprobar traducciones, hacer los manuales en PDF, los paquetes de Linux y la web |

Después de cambiar algo:

```bash
python3 build.py                          # vuelve a generar comunitat.py
python3 eines/comprova-traduccions.py     # comprueba que no falta ninguna traducción
python3 tests/prova_servidor.py           # pasa las pruebas del servidor
python3 comunitat.py                      # pruébalo
```

Otras herramientas:

```bash
python3 eines/paquet-linux.py             # hace el .deb y el .tar.gz en dist/
sh eines/manuals-pdf.sh dist/manuals      # hace los manuales en PDF (hace falta Chrome o Chromium)
python3 eines/web.py _site                # genera la web, con la prueba en el navegador
python3 eines/captures.py                 # vuelve a hacer las capturas de los manuales (hace falta Playwright)
```

## Publicar una versión

Cada vez que se suben cambios a `main`, [`.github/workflows/proves.yml`](.github/workflows/proves.yml) genera el programa y pasa las pruebas en Windows y Linux. Para publicar, GitHub lo hace todo solo con [`.github/workflows/publica.yml`](.github/workflows/publica.yml): prueba el programa (también la ventana propia), hace el instalador y el portable de Windows, el `.deb` y el `.tar.gz` de Linux y los manuales en PDF, y lo publica en [Releases](../../releases).

1. Cambia `VERSION` en `src/servidor.py` (por ejemplo, `"2.1"`) y vuelve a generar `comunitat.py` con `python3 build.py`.
2. Sube los cambios y una etiqueta en minúscula con el mismo número:

```bash
git tag v2.1
git push origin main v2.1
```

Al cabo de unos minutos, la versión nueva aparece en [Releases](../../releases). Si la etiqueta y `VERSION` no coinciden, la publicación se detiene y lo avisa.

La [web](https://jossanmar9.github.io/comunitat-del-anell/es/) se publica sola con [`.github/workflows/web.yml`](.github/workflows/web.yml) cada vez que se suben cambios a `main` (hace falta **Settings → Pages → Source: GitHub Actions**).

## Colaborar

Las propuestas de mejora y las correcciones son bienvenidas. Si has encontrado un error o tienes una idea, abre una [incidencia](../../issues).

## Uso de inteligencia artificial

Este proyecto se ha hecho con ayuda de IA:
- **Imágenes:** el mapa de ejemplo (en castellano y en valenciano), el logo y los retratos de los personajes se han generado con IA. Los retratos parten de las descripciones de los libros, con un estilo propio, y no reproducen a ningún actor ni las ilustraciones oficiales del juego.
- **Código y documentación:** el programa, las traducciones, los README, los manuales, los paquetes y la web se han escrito con un asistente de IA (Claude, de Anthropic) y se han revisado a mano.

## Licencia

[GPL-3.0](LICENSE) o posterior. Lo podéis usar, copiar, modificar y compartir libremente. Si publicáis una versión modificada, también tiene que ser libre y con el código abierto.

Las tipografías [Alegreya](https://github.com/huertatipografica/Alegreya) e [IM Fell English](https://iginomarini.com/fell/) son libres, con la licencia SIL Open Font License ([`src/web/fonts/`](src/web/fonts/)). En Windows, la ventana usa [pywebview](https://pywebview.flowrl.com/) (licencia BSD).

**Aviso:** proyecto de fans **no oficial**, sin relación con Z-Man Games, Asmodee ni Middle-earth Enterprises. «El Señor de los Anillos» y los nombres relacionados son marcas de sus propietarios. Este programa no incluye ningún componente del juego: para jugar hay que tenerlo.
