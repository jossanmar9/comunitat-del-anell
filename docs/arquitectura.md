# Arquitectura i comprovacions

Des de la v3, una sola persona porta la partida i **tota la lògica és a l'app web** (`src/web/`). És la mateixa a totes les plataformes; només canvia on es guarden els fitxers:

| Plataforma | Què fa de «disc» (`src/web/magatzem.js`) |
|---|---|
| Windows i Linux | `src/servidor.py`: un servidor HTTP lligat a `127.0.0.1` que llig i escriu fitxers JSON a la carpeta de dades. L'app es mostra en una finestra pròpia (`src/finestra.py`: pywebview/WebView2 o WebKitGTK). |
| Android | La mateixa pàgina dins de Capacitor; els fitxers van a IndexedDB. Exportar fa servir els connectors Filesystem i Share. |
| Navegador | La mateixa pàgina com a PWA (`build.py --web`), amb IndexedDB i un service worker per a funcionar sense connexió. |

`magatzem.js` fa les partides, l'historial, les còpies de seguretat (en obrir i cada 30 minuts, les 15 últimes), exportar i importar, sempre amb les rutes de sempre: `partides/<id>.json`, `partides/esborrades/`, `copies/<id>/<data>-<motiu>.json`, `historial.json`, `comunitat.json` (la partida oberta) i `mapa.json`. Així, una carpeta de la v2 es continua llegint.

**Seguretat del programa d'escriptori.** Escolta només a `127.0.0.1`; rebutja qualsevol `Host` que no siga `127.0.0.1:port` o `localhost:port` (contra el *DNS rebinding*); les escriptures han de portar la capçalera `X-Comunitat: 1`, que una altra web no pot posar sense permís del navegador; les rutes passen per una llista blanca d'expressions regulars; i cada fitxer s'escriu en un temporal amb `fsync` i substitució atòmica. Un fitxer danyat es reanomena `.danyat` en compte de sobreescriure'l. Un bloqueig (`comunitat.lock`) impedeix obrir dues vegades la mateixa carpeta de dades.

**De la v2 a la v3** (`migra_v2` a `src/persistencia.py`). Si `comunitat.sqlite3` tenia una foto pendent de passar als JSON, s'hi passa; després la base de dades es mou a `copies/v2/`. De `comunitat.json` es lleva el que era de la sala (jugadors, PIN i sessions).

`build.py` genera `comunitat.py` (un sol fitxer, amb la pàgina, les tipografies, els retrats i els mapes dins) i, amb `--web`, l'app web. Les compilacions són deterministes.

Comprovacions abans de publicar:

```bash
python3 build.py
python3 eines/comprova-traduccions.py
python3 tests/prova_servidor.py
python3 tests/prova_persistencia.py
python3 tests/prova_magatzem.py      # cal Node.js
python3 tests/prova_app.py           # cal Playwright amb Chromium
python3 eines/web.py /tmp/comunitat-web

git diff --check
```

`prova_app.py` juga una partida sencera en Chromium, tant amb el programa d'escriptori com amb l'app web: preparar, jugar, recarregar, perdre (historial), desfer, còpies i restaurar, duplicar, esborrar i recuperar, exportar i importar, canviar el mapa i l'idioma. GitHub repeteix les proves en Python 3.8 i 3.13, a Windows i Linux, prova les finestres natives dels paquets i fa l'APK.
