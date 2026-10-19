<p align="center"><img src="logo.png" alt="Logo de La Comunitat de l'Anell" width="180"></p>

# La Comunitat de l'Anell

**Valencià** · [Castellano](README.es.md) · [Web](https://jossanmar9.github.io/comunitat-del-anell/) · [Prova-la al navegador](https://jossanmar9.github.io/comunitat-del-anell/prova/)

Ajudant de taula, lliure i en valencià i castellà, per a portar les partides d'**«El Señor de los Anillos: El Destino de la Comunidad»**. Per a Windows i Linux.

El tauler i les peces els teniu a la taula. L'app porta els comptes:
- l'esperança i l'amenaça;
- els passos del torn;
- quants daus heu de tirar en cada tirada i què perdeu amb el resultat;
- els objectius, amb un registre de tot el que passa i un botó per a desfer.

Un ordinador fa de servidor i la resta hi entren des del navegador, mòbils inclosos, sense Internet.

![La pantalla de joc](docs/imatges/ca/05-partida.jpg)

## Descàrrega

Tot és a la pàgina de [descàrregues](../../releases/latest):

| Sistema | Fitxer |
|---|---|
| Windows 10/11 (recomanat) | `LaComunitat-X.Y-installador.exe`: no demana permisos d'administrador |
| Windows portable | `LaComunitat-X.Y-windows-portable.zip`: descomprimeix-lo i obri `LaComunitat.exe` |
| Ubuntu, Debian, Linux Mint… | `comunitat-del-anell_X.Y_all.deb` |
| Altres Linux | `LaComunitat-X.Y-linux.tar.gz`: descomprimeix-lo i obri `comunitat-del-anell.sh` |

En obrir-la, apareix una finestreta amb l'adreça i un **codi QR**, i el navegador ja amb l'app. Cada jugador escaneja el QR amb el mòbil i entra amb el seu nom.

Manuals (també en PDF dins de cada paquet):
- [Guia d'instal·lació](docs/guia-installacio.md): Windows, Linux, on es guarden les dades i opcions.
- [Manual d'usuari](docs/manual-usuari.md): tota l'app, pas a pas amb captures.

## Què fa

- **Pistes:** esperança (de 0 a 8), nivell d'amenaça (quantes cartes d'Ombra es roben), cartes «El cel s'enfosqueix» eixides, cartes que queden al mazo, objectius completats i ronda.
- **El torn pas a pas:** les 4 + 1 accions, robar 2 cartes (descompta el mazo i resta esperança si s'acaba) i resoldre les cartes d'Ombra que toquen.
- **Tirades de cerca i de batalla:** diu quants daus s'han de tirar. Quan hi anoteu el resultat, aplica la pèrdua d'esperança i diu quantes tropes s'han de llevar de cada bàndol. Té en compte els refugis, els natzguls i el valor gastat.
- **El cel s'enfosqueix, posar-se l'Anell i destruir l'Anell Únic**, cadascun amb el seu càlcul.
- **Preparació:** nivells de dificultat, escenaris suggerits, els 24 objectius i la llista de preparació del tauler, pas a pas.
- **Registre** de tot el que passa i **desfer** fins a 30 passos.
- **Resum en acabar** i **historial** de totes les partides acabades, amb victòries i derrotes per dificultat.
- **Diverses partides guardades.**
- **Retrats il·lustrats** dels 13 personatges jugables.
- **Mode fosc**, automàtic o triat a mà, i **adaptada al mòbil**. Tots els aparells connectats veuen els canvis al moment.
- **En valencià i en castellà.** Cada jugador tria l'idioma amb els botons VAL i CAS.

<p>
  <img src="docs/imatges/ca/21-mobil.jpg" alt="L'app en un mòbil" width="220">
  <img src="docs/imatges/ca/11-cerca-daus.jpg" alt="Anotar una tirada de cerca" width="460">
</p>

<p align="center"><img src="docs/imatges/personatges.webp" alt="Els retrats dels personatges" width="640"></p>

## El mapa

Al centre de la pantalla es mostra un mapa il·lustrat de la Terra Mitjana, en valencià o en castellà segons l'idioma de cada jugador. Per a posar el teu, copia la imatge a la carpeta de dades (el botó **Carpeta de dades** de la finestra l'obri) amb el nom `mapa.jpg` o `mapa.png`. Si el tens en els dos idiomes, anomena'ls `mapa-val.jpg` i `mapa-es.jpg`.

## Sense instal·lar: amb Python

A Mac, o si prefereixes no instal·lar res, només cal **Python 3.8 o més nou**:

```bash
python3 comunitat.py
```

A Windows, fes doble clic a `arrancar-windows.bat`. Les opcions (`--port`, `--partida`, `--dades`, `--sense-finestra`…) estan a la [guia d'instal·lació](docs/guia-installacio.md#opcions).

## Modificar el programa

`comunitat.py` es genera a partir dels fitxers de `src/`, i és l'únic fitxer que cal per a fer-lo anar:

| Fitxer | Què hi ha |
|---|---|
| `src/servidor.py` | El servidor (Python, sense dependències) |
| `src/finestra.py` | La finestreta amb l'adreça i el QR (Tk) |
| `src/qr.py` | El generador de codis QR |
| `src/mapes/` | Els mapes d'exemple, que van dins del programa |
| `src/web/app.js` | La lògica de la pàgina |
| `src/web/dades.js` | Personatges, objectius, escenaris i preparació |
| `src/web/personatges/` | Els retrats dels personatges (WebP de 200 px) |
| `src/web/i18n.js` | Les traduccions al castellà (per a afegir un idioma, copia el bloc `es`) |
| `src/web/estil-base.css`, `src/web/estil.css` | L'estil |
| `src/web/cos.html` | L'estructura de la pàgina |

Després de canviar alguna cosa, torna a generar el programa i comprova les traduccions:

```bash
python3 build.py
python3 eines/comprova-traduccions.py
```

Altres eines:

| Fitxer | Què fa |
|---|---|
| `docs/*.md` | Els manuals. Les captures són a `docs/imatges/`. |
| `eines/manuals-pdf.sh` | Fa els manuals en PDF (cal Chrome o Chromium). |
| `eines/paquet-linux.py` | Fa el `.deb` i el `.tar.gz`. |
| `paquets/` | L'instal·lador de Windows (Inno Setup) i els fitxers del menú de Linux. |
| `eines/web.py` | Fa la web de GitHub Pages, amb la prova al navegador. |

### Publicar una versió

GitHub ho fa tot sol ([`.github/workflows/publica.yml`](.github/workflows/publica.yml)): prova el programa, fa els manuals en PDF, l'instal·lador i el portable de Windows, i els paquets de Linux. Cal:

1. Canviar `VERSION` a `src/servidor.py` (per exemple, `2.0`) i tornar a generar `comunitat.py`.
2. Pujar els canvis i crear l'etiqueta de la versió en minúscula, `v2.0`, des de **Releases → Draft a new release** (o amb `git tag v2.0` i `git push origin v2.0`).

Al cap d'uns minuts, els fitxers apareixen a [Releases](../../releases). Si l'etiqueta i `VERSION` no coincideixen, no es publica res.

La web es publica sola en cada canvi a `main` ([`.github/workflows/web.yml`](.github/workflows/web.yml)). Cal tindre **Settings → Pages → Source** en «GitHub Actions».

Les propostes de millora i les correccions són benvingudes.

## Llicència

[GPL-3.0](LICENSE) o posterior. El podeu usar, copiar, modificar i compartir lliurement. Si en publiqueu una versió modificada, també ha de ser lliure i amb el codi obert.

## Ús d'intel·ligència artificial

Aquest projecte s'ha fet amb ajuda d'IA:
- **Imatges:** el mapa d'exemple (en valencià i en castellà), el logo i els retrats dels personatges s'han generat amb IA. Els retrats parteixen de les descripcions dels llibres, amb un estil propi, i no reprodueixen cap actor ni les il·lustracions oficials del joc.
- **Codi i documentació:** el programa, els paquets, la web, les traduccions, els README i els manuals s'han escrit amb un assistent d'IA (Claude, d'Anthropic) i s'han revisat a mà.

## Avís

Projecte de fans **no oficial**, sense relació amb Z-Man Games, Asmodee ni Middle-earth Enterprises. «El Señor de los Anillos» i els noms relacionats són marques dels seus propietaris. Aquest programa no inclou cap component del joc: per a jugar cal tindre'l.
