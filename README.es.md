<p align="center"><img src="logo.png" alt="Logo de La Comunidad del Anillo" width="180"></p>

# La Comunidad del Anillo

[Valencià](README.md) · **Castellano** · [Web](https://jossanmar9.github.io/comunitat-del-anell/es/) · [Pruébala en el navegador](https://jossanmar9.github.io/comunitat-del-anell/prova/)

Ayudante de mesa, libre y en castellano y valenciano, para llevar las partidas de **«El Señor de los Anillos: El Destino de la Comunidad»**. Para Windows y Linux.

El tablero y las piezas los tenéis en la mesa. La app lleva las cuentas:
- la Esperanza y la Amenaza;
- los pasos del turno;
- cuántos dados tenéis que tirar en cada tirada y qué perdéis con el resultado;
- los objetivos, con un registro de todo lo que pasa y un botón para deshacer.

Un ordenador hace de servidor y los demás entran desde el navegador, móviles incluidos, sin Internet.

![La pantalla de juego](docs/imatges/es/05-partida.jpg)

## Descarga

Todo está en la página de [descargas](../../releases/latest):

| Sistema | Archivo |
|---|---|
| Windows 10/11 (recomendado) | `LaComunitat-X.Y-installador.exe`: no pide permisos de administrador |
| Windows portable | `LaComunitat-X.Y-windows-portable.zip`: descomprímelo y abre `LaComunitat.exe` |
| Ubuntu, Debian, Linux Mint… | `comunitat-del-anell_X.Y_all.deb` |
| Otros Linux | `LaComunitat-X.Y-linux.tar.gz`: descomprímelo y abre `comunitat-del-anell.sh` |

Al abrirla, aparece una ventanita con la dirección y un **código QR**, y el navegador ya con la app. Cada jugador escanea el QR con el móvil y entra con su nombre.

Manuales (también en PDF dentro de cada paquete):
- [Guía de instalación](docs/guia-instalacion.md): Windows, Linux, dónde se guardan los datos y opciones.
- [Manual de usuario](docs/manual-usuario.md): toda la app, paso a paso con capturas.

## Qué hace

- **Marcadores:** Esperanza (de 0 a 8), nivel de Amenaza (cuántas cartas de Sombra se roban), cartas «El cielo se oscurece» salidas, cartas que quedan en el mazo, objetivos completados y ronda.
- **El turno paso a paso:** las 4 + 1 acciones, robar 2 cartas (descuenta el mazo y resta Esperanza si se acaba) y resolver las cartas de Sombra que tocan.
- **Tiradas de búsqueda y de batalla:** dice cuántos dados hay que tirar. Cuando anotáis el resultado, aplica la pérdida de Esperanza y dice cuántas Tropas hay que quitar de cada bando. Tiene en cuenta los Refugios, los Nazgûl y la Heroicidad gastada.
- **El cielo se oscurece, ponerse el Anillo y destruir el Anillo Único**, cada uno con su cálculo.
- **Preparación:** niveles de dificultad, escenarios sugeridos, los 24 objetivos y la lista de preparación del tablero, paso a paso.
- **Registro** de todo lo que pasa y **deshacer** hasta 30 pasos.
- **Resumen al terminar** e **historial** de todas las partidas terminadas, con victorias y derrotas por dificultad.
- **Varias partidas guardadas.**
- **Retratos ilustrados** de los 13 personajes jugables.
- **Modo oscuro**, automático o elegido a mano, y **adaptada al móvil**. Todos los dispositivos conectados ven los cambios al momento.
- **En castellano y en valenciano.** Cada jugador elige el idioma con los botones CAS y VAL.

<p>
  <img src="docs/imatges/es/21-mobil.jpg" alt="La app en un móvil" width="220">
  <img src="docs/imatges/es/11-cerca-daus.jpg" alt="Anotar una tirada de búsqueda" width="460">
</p>

<p align="center"><img src="docs/imatges/personatges.webp" alt="Los retratos de los personajes" width="640"></p>

## El mapa

En el centro de la pantalla se muestra un mapa ilustrado de la Tierra Media, en castellano o en valenciano según el idioma de cada jugador. Para poner el tuyo, copia la imagen en la carpeta de datos (el botón **Carpeta de datos** de la ventana la abre) con el nombre `mapa.jpg` o `mapa.png`. Si lo tienes en los dos idiomas, llámalos `mapa-es.jpg` y `mapa-val.jpg`.

## Sin instalar: con Python

En Mac, o si prefieres no instalar nada, solo hace falta **Python 3.8 o más nuevo**:

```bash
python3 comunitat.py
```

En Windows, haz doble clic en `arrancar-windows.bat`. Las opciones (`--port`, `--partida`, `--dades`, `--sense-finestra`…) están en la [guía de instalación](docs/guia-instalacion.md#opciones).

## Modificar el programa

`comunitat.py` se genera a partir de los archivos de `src/`, y es el único archivo necesario para que funcione:

| Archivo | Qué hay |
|---|---|
| `src/servidor.py` | El servidor (Python, sin dependencias) |
| `src/finestra.py` | La ventanita con la dirección y el QR (Tk) |
| `src/qr.py` | El generador de códigos QR |
| `src/mapes/` | Los mapas de ejemplo, que van dentro del programa |
| `src/web/app.js` | La lógica de la página |
| `src/web/dades.js` | Personajes, objetivos, escenarios y preparación |
| `src/web/personatges/` | Los retratos de los personajes (WebP de 200 px) |
| `src/web/i18n.js` | Las traducciones al castellano (para añadir un idioma, copia el bloque `es`) |
| `src/web/estil-base.css`, `src/web/estil.css` | El estilo |
| `src/web/cos.html` | La estructura de la página |

Después de cambiar algo, vuelve a generar el programa y comprueba las traducciones:

```bash
python3 build.py
python3 eines/comprova-traduccions.py
```

Otras herramientas:

| Archivo | Qué hace |
|---|---|
| `docs/*.md` | Los manuales. Las capturas están en `docs/imatges/`. |
| `eines/manuals-pdf.sh` | Hace los manuales en PDF (hace falta Chrome o Chromium). |
| `eines/paquet-linux.py` | Hace el `.deb` y el `.tar.gz`. |
| `paquets/` | El instalador de Windows (Inno Setup) y los archivos del menú de Linux. |
| `eines/web.py` | Hace la web de GitHub Pages, con la prueba en el navegador. |

### Publicar una versión

GitHub lo hace todo solo ([`.github/workflows/publica.yml`](.github/workflows/publica.yml)): prueba el programa, hace los manuales en PDF, el instalador y el portable de Windows, y los paquetes de Linux. Hay que:

1. Cambiar `VERSION` en `src/servidor.py` (por ejemplo, `2.0`) y volver a generar `comunitat.py`.
2. Subir los cambios y crear la etiqueta de la versión en minúscula, `v2.0`, desde **Releases → Draft a new release** (o con `git tag v2.0` y `git push origin v2.0`).

Al cabo de unos minutos, los archivos aparecen en [Releases](../../releases). Si la etiqueta y `VERSION` no coinciden, no se publica nada.

La web se publica sola con cada cambio en `main` ([`.github/workflows/web.yml`](.github/workflows/web.yml)). Hay que tener **Settings → Pages → Source** en «GitHub Actions».

Las propuestas de mejora y las correcciones son bienvenidas.

## Licencia

[GPL-3.0](LICENSE) o posterior. Lo podéis usar, copiar, modificar y compartir libremente. Si publicáis una versión modificada, también tiene que ser libre y con el código abierto.

## Uso de inteligencia artificial

Este proyecto se ha hecho con ayuda de IA:
- **Imágenes:** el mapa de ejemplo (en castellano y en valenciano), el logo y los retratos de los personajes se han generado con IA. Los retratos parten de las descripciones de los libros, con un estilo propio, y no reproducen a ningún actor ni las ilustraciones oficiales del juego.
- **Código y documentación:** el programa, los paquetes, la web, las traducciones, los README y los manuales se han escrito con un asistente de IA (Claude, de Anthropic) y se han revisado a mano.

## Aviso

Proyecto de fans **no oficial**, sin relación con Z-Man Games, Asmodee ni Middle-earth Enterprises. «El Señor de los Anillos» y los nombres relacionados son marcas de sus propietarios. Este programa no incluye ningún componente del juego: para jugar hay que tenerlo.
