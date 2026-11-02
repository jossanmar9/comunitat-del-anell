#!/usr/bin/env python3
"""Genera la web de presentació de La Comunitat (GitHub Pages) en valencià i castellà.

Ús:  python3 eines/web.py [carpeta-eixida]        (per defecte, _site)

Agafa la versió de src/servidor.py, unes quantes captures de docs/imatges i el logotip, i fa la
app web (app/): la mateixa app, que es pot instal·lar i funciona sense connexió (build.py --web).
Els manuals en PDF els afig el workflow (.github/workflows/web.yml) a la carpeta pdf/.
Sense dependències. Llicència GPL-3.0-or-later.
"""
import datetime
import html
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "https://github.com/jossanmar9/comunitat-del-anell"
WEB = "https://jossanmar9.github.io/comunitat-del-anell/"

CAPTURES = ["05-partida", "00-inici", "03-preparacio", "04-comunitat", "07-torn", "11-cerca-daus", "13-batalla-daus",
            "09-cel", "18-resum", "19-partides", "22-copies", "20-historial", "21-mobil"]

def capture_filename(name):
    return name + (".png" if (ROOT / "docs/imatges/ca" / (name + ".png")).exists() else ".jpg")


T = {
    "ca": {
        "nom": "La Comunitat",
        "lang": "ca-valencia", "altre": "es", "altre_nom": "Castellano", "altre_url": "es/",
        "titol": "La Comunitat: ajudant lliure per a «El Destino de la Comunidad»",
        "descripcio": "Programa lliure i gratuït per a portar les partides del joc de taula «El Señor de los Anillos: "
                      "El Destino de la Comunidad», en valencià i castellà: esperança, amenaça, torns, tirades i objectius. "
                      "Per a Windows, Linux i Android, i també al navegador.",
        "lema": "Ajudant lliure per al joc de taula",
        "hero": "El tauler a la taula. Els comptes, a l'app.",
        "hero_text": "Per a «El Señor de los Anillos: El Destino de la Comunidad». Una persona porta la partida des de "
                     "l'ordinador, la tauleta o el mòbil: l'esperança, l'amenaça, el torn pas a pas i els daus de cada "
                     "tirada, sempre al dia. Sense Internet, sense comptes ni quotes, en valencià i castellà.",
        "baixa_win": "Windows", "baixa_linux": "Linux", "baixa_android": "Android",
        "versio": "Versió {v} · Windows 10 i 11 · Ubuntu, Debian, Fedora, Arch… · Android 5.1 o més nou · Gratuït i lliure",
        "manual": "Llig el manual", "prova": "Usa-la al navegador",
        "nav_que": "Què fa", "nav_veure": "Captures", "nav_com": "Com començar", "nav_codi": "Codi",
        "que_titol": "Què porta La Comunitat",
        "que_intro": "Les cartes, les tropes i els natzguls continuen al tauler. L'app s'encarrega dels comptes que s'obliden.",
        "moduls": [
            ("Pistes", "Esperança, amenaça, cartes de la baralla, cels enfosquits, objectius i ronda, sempre a la vista i amb desfer."),
            ("El torn pas a pas", "Les 4 + 1 accions, robar 2 cartes i resoldre les cartes d'Ombra que toquen, en l'ordre del manual."),
            ("Tirades de cerca", "Quants daus tirar segons els natzguls i les tropes, i què es perd amb el resultat. Amb refugis i Mordor."),
            ("Batalles", "Atac o provocada per l'Ombra: daus, valor gastat i quantes tropes s'han de llevar de cada bàndol."),
            ("El cel s'enfosqueix", "Els quatre passos de la carta, «Et veig!» inclòs, i també posar-se l'Anell i destruir-lo."),
            ("Preparació", "Cinc nivells de dificultat, escenaris suggerits, els 24 objectius i la llista del tauler pas a pas."),
            ("Resum, historial i còpies", "En acabar, on s'ha perdut l'esperança i quantes tirades hi ha hagut. L'historial de totes les partides, còpies automàtiques i exportar."),
            ("On vulgues", "Finestra pròpia a Windows i Linux, app per a Android i app web que funciona sense connexió. El mapa, el que tu vulgues. Mode fosc i dos idiomes."),
        ],
        "veure_titol": "Així es veu",
        "veure_intro": "Captures reals de l'app. Usa les fletxes o les miniatures.",
        "anterior": "Captura anterior", "seguent": "Captura següent", "canvis": "Historial de canvis",
        "captures": {
            "05-partida": "La pantalla de joc: les eines, el mapa i el torn pas a pas.",
            "00-inici": "En obrir-la per primera vegada: crear una partida o obrir-ne una de guardada.",
            "03-preparacio": "La preparació: dificultat, participants, personatges i objectius.",
            "04-comunitat": "La pestanya Comunitat: la llista de preparació del tauler i qui porta cada personatge.",
            "07-torn": "Els passos del torn, en l'ordre del manual.",
            "11-cerca-daus": "Una tirada de cerca: l'app diu quants daus tirar i aplica el resultat.",
            "13-batalla-daus": "Una batalla: els resultats dels daus i el valor gastat.",
            "09-cel": "El cel s'enfosqueix, amb els quatre passos de la carta.",
            "18-resum": "El resum en acabar: on s'ha perdut l'esperança i quantes tirades hi ha hagut.",
            "19-partides": "Les partides guardades: obrir, duplicar, exportar i importar.",
            "22-copies": "Les còpies de seguretat de cada partida.",
            "20-historial": "L'historial de totes les partides acabades.",
            "21-mobil": "Al mòbil o a l'app d'Android, en una sola columna.",
        },
        "com_titol": "Com començar",
        "passos": [
            ("Tria on", "A l'ordinador, baixa l'instal·lador de Windows (o el <code>.zip</code> portable), el "
                        "<code>.deb</code> d'Ubuntu i Debian o el <code>.tar.gz</code> per a la resta de Linux. "
                        "A Android, l'<code>.apk</code>. O, sense instal·lar res, obri <a href=\"app/\">l'app web</a> "
                        "i afig-la a la pantalla d'inici."),
            ("Crea una partida", "Posa-li un nom, tria la dificultat, els participants i els objectius. L'app et diu "
                                 "com preparar el tauler."),
            ("Juga", "El tauler mana; l'app porta els comptes i et guia pas a pas en cada torn. Tot es guarda tot "
                     "sol: pots tancar-la i continuar un altre dia."),
        ],
        "dades_titol": "Tot es queda a casa",
        "dades": [
            "No cal Internet ni crear cap compte. L'app no envia res enlloc.",
            "Les partides es guarden a l'aparell, amb còpies de seguretat automàtiques.",
            "Les pots exportar en un fitxer i obrir-les en un altre ordinador o mòbil.",
            "Les lletres i les imatges van dins de l'app: no es connecta a cap servidor de fora.",
        ],
        "req_titol": "Què cal",
        "req": ["El joc de taula «El Señor de los Anillos: El Destino de la Comunidad»",
                "Un ordinador amb Windows 10 o 11 de 64 bits o amb Linux, un mòbil o tauleta Android, "
                "o qualsevol navegador actual"],
        "docs_titol": "Manuals",
        "docs": [("manual-usuari.pdf", "Manual d'usuari, pas a pas amb captures"),
                 ("guia-installacio.pdf", "Guia d'instal·lació per a Windows, Linux i Android")],
        "lliure_titol": "Programari lliure",
        "lliure": "La Comunitat es distribueix sota la llicència GPL-3.0 o posterior: la pots utilitzar, "
                  "estudiar, modificar i compartir. El codi és públic a GitHub.",
        "ia": "S'ha desenvolupat amb l'ajuda d'una intel·ligència artificial (Claude, d'Anthropic). El mapa d'exemple, "
              "el logotip i els retrats dels personatges s'han generat amb IA.",
        "codi": "Codi a GitHub",
        "errades": "Has trobat una errada o tens una proposta? Obri una incidència a GitHub.",
        "avis": "Projecte de fans no oficial, sense relació amb Z-Man Games, Asmodee ni Middle-earth Enterprises. "
                "«El Señor de los Anillos» i els noms relacionats són marques dels seus propietaris. Per a jugar cal tindre el joc.",
        "tema": "Mode fosc o clar",
    },
    "es": {
        "nom": "La Comunidad",
        "lang": "es", "altre": "ca", "altre_nom": "Valencià", "altre_url": "../",
        "titol": "La Comunidad: ayudante libre para «El Destino de la Comunidad»",
        "descripcio": "Programa libre y gratuito para llevar las partidas del juego de mesa «El Señor de los Anillos: "
                      "El Destino de la Comunidad», en castellano y valenciano: Esperanza, Amenaza, turnos, tiradas y "
                      "objetivos. Para Windows, Linux y Android, y también en el navegador.",
        "lema": "Ayudante libre para el juego de mesa",
        "hero": "El tablero en la mesa. Las cuentas, en la app.",
        "hero_text": "Para «El Señor de los Anillos: El Destino de la Comunidad». Una persona lleva la partida desde el "
                     "ordenador, la tableta o el móvil: la Esperanza, la Amenaza, el turno paso a paso y los dados de "
                     "cada tirada, siempre al día. Sin Internet, sin cuentas ni cuotas, en castellano y valenciano.",
        "baixa_win": "Windows", "baixa_linux": "Linux", "baixa_android": "Android",
        "versio": "Versión {v} · Windows 10 y 11 · Ubuntu, Debian, Fedora, Arch… · Android 5.1 o posterior · Gratuito y libre",
        "manual": "Leer el manual", "prova": "Úsala en el navegador",
        "nav_que": "Qué hace", "nav_veure": "Capturas", "nav_com": "Cómo empezar", "nav_codi": "Código",
        "que_titol": "Qué lleva La Comunidad",
        "que_intro": "Las cartas, las Tropas y los Nazgûl siguen en el tablero. La app se encarga de las cuentas que se olvidan.",
        "moduls": [
            ("Marcadores", "Esperanza, Amenaza, cartas del mazo, cielos oscurecidos, objetivos y ronda, siempre a la vista y con deshacer."),
            ("El turno paso a paso", "Las 4 + 1 acciones, robar 2 cartas y resolver las cartas de Sombra que tocan, en el orden del reglamento."),
            ("Tiradas de búsqueda", "Cuántos dados tirar según los Nazgûl y las Tropas, y qué se pierde con el resultado. Con Refugios y Mordor."),
            ("Batallas", "Ataque o provocada por la Sombra: dados, Heroicidad gastada y cuántas Tropas hay que quitar de cada bando."),
            ("El cielo se oscurece", "Los cuatro pasos de la carta, «¡Te veo!» incluido, y también ponerse el Anillo y destruirlo."),
            ("Preparación", "Cinco niveles de dificultad, escenarios sugeridos, los 24 objetivos y la lista del tablero paso a paso."),
            ("Resumen, historial y copias", "Al terminar, dónde se ha perdido la Esperanza y cuántas tiradas ha habido. El historial de todas las partidas, copias automáticas y exportar."),
            ("Donde quieras", "Ventana propia en Windows y Linux, app para Android y app web que funciona sin conexión. El mapa, el que tú quieras. Modo oscuro y dos idiomas."),
        ],
        "veure_titol": "Así se ve",
        "veure_intro": "Capturas reales de la app. Usa las flechas o las miniaturas.",
        "anterior": "Captura anterior", "seguent": "Captura siguiente", "canvis": "Historial de cambios",
        "captures": {
            "05-partida": "La pantalla de juego: las herramientas, el mapa y el turno paso a paso.",
            "00-inici": "Al abrirla por primera vez: crear una partida o abrir una guardada.",
            "03-preparacio": "La preparación: dificultad, participantes, personajes y objetivos.",
            "04-comunitat": "La pestaña Comunidad: la lista de preparación del tablero y quién lleva cada personaje.",
            "07-torn": "Los pasos del turno, en el orden del reglamento.",
            "11-cerca-daus": "Una tirada de búsqueda: la app dice cuántos dados tirar y aplica el resultado.",
            "13-batalla-daus": "Una batalla: los resultados de los dados y la Heroicidad gastada.",
            "09-cel": "El cielo se oscurece, con los cuatro pasos de la carta.",
            "18-resum": "El resumen al terminar: dónde se ha perdido la Esperanza y cuántas tiradas ha habido.",
            "19-partides": "Las partidas guardadas: abrir, duplicar, exportar e importar.",
            "22-copies": "Las copias de seguridad de cada partida.",
            "20-historial": "El historial de todas las partidas terminadas.",
            "21-mobil": "En el móvil o en la app de Android, en una sola columna.",
        },
        "com_titol": "Cómo empezar",
        "passos": [
            ("Elige dónde", "En el ordenador, descarga el instalador de Windows (o el <code>.zip</code> portable), el "
                            "<code>.deb</code> de Ubuntu y Debian o el <code>.tar.gz</code> para el resto de Linux. "
                            "En Android, el <code>.apk</code>. O, sin instalar nada, abre <a href=\"../app/\">la app web</a> "
                            "y añádela a la pantalla de inicio."),
            ("Crea una partida", "Ponle un nombre, elige la dificultad, los participantes y los objetivos. La app te "
                                 "dice cómo preparar el tablero."),
            ("Juega", "El tablero manda; la app lleva las cuentas y te guía paso a paso en cada turno. Todo se guarda "
                      "solo: puedes cerrarla y seguir otro día."),
        ],
        "dades_titol": "Todo se queda en casa",
        "dades": [
            "No hace falta Internet ni crear ninguna cuenta. La app no envía nada a ningún sitio.",
            "Las partidas se guardan en el dispositivo, con copias de seguridad automáticas.",
            "Las puedes exportar en un archivo y abrirlas en otro ordenador o móvil.",
            "Las letras y las imágenes van dentro de la app: no se conecta a ningún servidor de fuera.",
        ],
        "req_titol": "Qué hace falta",
        "req": ["El juego de mesa «El Señor de los Anillos: El Destino de la Comunidad»",
                "Un ordenador con Windows 10 u 11 de 64 bits o con Linux, un móvil o tableta Android, "
                "o cualquier navegador actual"],
        "docs_titol": "Manuales",
        "docs": [("manual-usuario.pdf", "Manual de usuario, paso a paso con capturas"),
                 ("guia-instalacion.pdf", "Guía de instalación para Windows, Linux y Android")],
        "lliure_titol": "Software libre",
        "lliure": "La Comunidad se distribuye bajo la licencia GPL-3.0 o posterior: la puedes usar, "
                  "estudiar, modificar y compartir. El código es público en GitHub.",
        "ia": "Se ha desarrollado con la ayuda de una inteligencia artificial (Claude, de Anthropic). El mapa de ejemplo, "
              "el logotipo y los retratos de los personajes se han generado con IA.",
        "codi": "Código en GitHub",
        "errades": "¿Has encontrado un error o tienes una propuesta? Abre una incidencia en GitHub.",
        "avis": "Proyecto de fans no oficial, sin relación con Z-Man Games, Asmodee ni Middle-earth Enterprises. "
                "«El Señor de los Anillos» y los nombres relacionados son marcas de sus propietarios. Para jugar hay que tener el juego.",
        "tema": "Modo oscuro o claro",
    },
}

ICONA_WIN = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M3 5.5 10 4.5v7H3zm8-1.2L21 3v8.5H11zM3 12.5h7v7L3 18.5zm8 0h10V21l-10-1.4z"/></svg>')
ICONA_ANDROID = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" '
                 'stroke-linecap="round" stroke-linejoin="round"><path d="M5 17V11a7 7 0 0 1 14 0v6z"/>'
                 '<path d="M8 4.5 9.3 6.6M16 4.5l-1.3 2.1"/><circle cx="9.5" cy="10.5" r=".6" fill="currentColor"/>'
                 '<circle cx="14.5" cy="10.5" r=".6" fill="currentColor"/><path d="M8 17v3M16 17v3"/></svg>')
ICONA_LINUX = ('<svg viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.8" '
               'stroke-linejoin="round"><path d="M12 3c-2.2 0-3.4 1.8-3.4 4.2 0 1.6-.4 2.7-1.4 4.1C5.8 13.2 5 15 5 16.8 '
               '5 19.3 7.6 21 12 21s7-1.7 7-4.2c0-1.8-.8-3.6-2.2-5.5-1-1.4-1.4-2.5-1.4-4.1C15.4 4.8 14.2 3 12 3z"/>'
               '<circle cx="10.3" cy="7.6" r=".6" fill="currentColor"/><circle cx="13.7" cy="7.6" r=".6" fill="currentColor"/>'
               '<path d="M10.6 9.8 12 10.8l1.4-1"/></svg>')


def versio():
    v = os.environ.get("COMUNITAT_VERSIO")
    if v:
        return v
    m = re.search(r'^VERSION = "([^"]+)"', (ROOT / "src" / "servidor.py").read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else ""


def e(s):
    return html.escape(s, quote=True)


def pagina(t, l, base, v):
    descarrega = REPO + "/releases/latest"
    moduls = "".join(f'<div class="modul"><dt>{e(n)}</dt><dd>{e(d)}</dd></div>' for n, d in t["moduls"])
    passos = "".join(f"<li><h3>{e(n)}</h3><p>{d}</p></li>" for n, d in t["passos"])
    dades = "".join(f"<li>{e(d)}</li>" for d in t["dades"])
    req = "".join(f"<li>{e(d)}</li>" for d in t["req"])
    docs = "".join(f'<li><a href="{base}pdf/{e(f)}">{e(n)}</a> <span class="pes">PDF</span></li>' for f, n in t["docs"])
    primera = CAPTURES[0]
    miniatures = ""
    for i, c in enumerate(CAPTURES):
        src = f"{base}img/{l}/{capture_filename(c)}"
        actual = ' aria-current="true"' if i == 0 else ""
        miniatures += (f'<li><button type="button" data-src="{e(src)}" data-peu="{e(t["captures"][c])}"{actual} '
                       f'aria-label="{e(t["captures"][c])}"><img src="{e(src)}" alt="" loading="lazy"></button></li>')
    any_ = datetime.date.today().year
    page = f"""<!doctype html>
<html lang="{t['lang']}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(t['titol'])}</title>
<meta name="description" content="{e(t['descripcio'])}">
<meta property="og:title" content="{e(t['titol'])}">
<meta property="og:description" content="{e(t['descripcio'])}">
<meta property="og:image" content="{WEB}img/{l}/{capture_filename(primera)}">
<link rel="icon" href="{base}img/icona.png">
<link rel="alternate" hreflang="{t['altre']}" href="{t['altre_url']}">
<link rel="stylesheet" href="{base}fonts/fonts.css">
<link rel="stylesheet" href="{base}estil.css">
<script>try{{var t=localStorage.getItem('cm-web-tema');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
</head>
<body>
<header class="barra">
  <a class="marca" href="./"><img src="{base}img/icona.png" alt="" width="40" height="40"><span>{e(t['nom'])}</span></a>
  <nav aria-label="Seccions">
    <a href="#que">{t['nav_que']}</a>
    <a href="#captures">{t['nav_veure']}</a>
    <a href="#comencar">{t['nav_com']}</a>
    <a href="{REPO}">{t['nav_codi']}</a>
    <a class="idioma" href="{t['altre_url']}" hreflang="{t['altre']}" lang="{t['altre']}">{t['altre_nom']}</a>
    <button class="tema" type="button" id="tema" title="{t['tema']}" aria-label="{t['tema']}">◐</button>
  </nav>
</header>

<main>
<section class="hero">
  <div class="hero-text">
    <p class="lema">{t['lema']}</p>
    <h1>{t['hero']}</h1>
    <p class="entrada">{t['hero_text']}</p>
    <div class="accions">
      <a class="boto" data-so="win" href="{descarrega}">{ICONA_WIN}{t['baixa_win']}</a>
      <a class="boto" data-so="linux" href="{descarrega}">{ICONA_LINUX}{t['baixa_linux']}</a>
      <a class="boto" data-so="android" href="{descarrega}">{ICONA_ANDROID}{t['baixa_android']}</a>
    </div>
    <p class="versio">{t['versio'].format(v=v)} · <a href="{base}app/">{t['prova']}</a> · <a href="{base}pdf/{t['docs'][0][0]}">{t['manual']}</a> · <a href="{REPO}/blob/main/CHANGELOG.md">{t['canvis']}</a></p>
  </div>
  <figure class="hero-captura">
    <img src="{base}img/{l}/{capture_filename(primera)}" alt="{e(t['captures'][primera])}" width="1600" height="1012">
  </figure>
</section>

<section id="que" class="seccio">
  <div class="cap">
    <h2>{t['que_titol']}</h2>
    <p>{t['que_intro']}</p>
  </div>
  <dl class="moduls">{moduls}</dl>
</section>

<section id="captures" class="seccio galeria" tabindex="0" aria-label="{t['veure_titol']}">
  <div class="cap">
    <h2>{t['veure_titol']}</h2>
    <p>{t['veure_intro']}</p>
  </div>
  <figure class="principal">
    <img id="captura" src="{base}img/{l}/{capture_filename(primera)}" alt="{e(t['captures'][primera])}">
    <div class="gallery-controls"><button type="button" id="gallery-prev" aria-label="{t['anterior']}" aria-controls="captura">←</button><span id="gallery-count" aria-live="polite">1 / {len(CAPTURES)}</span><button type="button" id="gallery-next" aria-label="{t['seguent']}" aria-controls="captura">→</button></div>
    <figcaption id="peu">{e(t['captures'][primera])}</figcaption>
  </figure>
  <ul class="miniatures" aria-label="{t['veure_titol']}">{miniatures}</ul>
</section>

<section id="comencar" class="seccio">
  <div class="cap"><h2>{t['com_titol']}</h2></div>
  <ol class="passos">{passos}</ol>
  <div class="accions">
    <a class="boto" data-so="win" href="{descarrega}">{ICONA_WIN}{t['baixa_win']}</a>
    <a class="boto" data-so="linux" href="{descarrega}">{ICONA_LINUX}{t['baixa_linux']}</a>
    <a class="boto" data-so="android" href="{descarrega}">{ICONA_ANDROID}{t['baixa_android']}</a>
  </div>
</section>

<section class="seccio dues">
  <div>
    <h2>{t['dades_titol']}</h2>
    <ul class="punts">{dades}</ul>
  </div>
  <div>
    <h2>{t['req_titol']}</h2>
    <ul class="punts">{req}</ul>
    <h2 class="h2-segon">{t['docs_titol']}</h2>
    <ul class="docs">{docs}</ul>
  </div>
</section>

<section class="seccio lliure">
  <h2>{t['lliure_titol']}</h2>
  <p>{t['lliure']}</p>
  <p class="nota">{t['ia']}</p>
  <p><a class="boto secundari" href="{REPO}">{t['codi']}</a></p>
  <p class="nota"><a href="{REPO}/issues">{t['errades']}</a></p>
</section>
</main>

<footer class="peu">
  <div class="orla" aria-hidden="true"><span>✦</span></div>
  <p><img src="{base}img/icona.png" alt="" width="28" height="28"> <span>{e(t['nom'])}, {any_}.</span> <a href="{REPO}/blob/main/LICENSE">GPL-3.0-or-later</a></p>
  <p class="avis">{t['avis']}</p>
</footer>

<script>
(function(){{
  var root=document.documentElement;
  // Destaca el botó de descàrrega del sistema del visitant
  var ua=navigator.userAgent,so=/Android/.test(ua)?'android':/Linux|X11/.test(ua)?'linux':'win';
  document.querySelectorAll('.boto[data-so]').forEach(function(b){{
    if(b.dataset.so!==so)b.classList.add('secundari');
  }});
  // Galeria: botons, teclat i gest horitzontal; no avança automàticament.
  var gallery=document.getElementById('captures');
  var thumbnails=Array.from(document.querySelectorAll('.miniatures button'));
  var current=0;
  function showCapture(index){{
    current=(index+thumbnails.length)%thumbnails.length;
    var button=thumbnails[current],img=document.getElementById('captura');
    img.src=button.dataset.src;img.alt=button.dataset.peu;
    document.getElementById('peu').textContent=button.dataset.peu;
    document.getElementById('gallery-count').textContent=(current+1)+' / '+thumbnails.length;
    thumbnails.forEach(function(b){{b.removeAttribute('aria-current')}});
    button.setAttribute('aria-current','true');
    var list=document.querySelector('.miniatures');
    list.scrollLeft=button.parentElement.offsetLeft-list.offsetLeft-list.clientWidth/2+button.offsetWidth/2;
  }}
  thumbnails.forEach(function(button,index){{button.addEventListener('click',function(){{showCapture(index)}})}});
  document.getElementById('gallery-prev').addEventListener('click',function(){{showCapture(current-1)}});
  document.getElementById('gallery-next').addEventListener('click',function(){{showCapture(current+1)}});
  gallery.addEventListener('keydown',function(event){{
    if(event.key==='ArrowRight'||event.key==='ArrowLeft'){{event.preventDefault();showCapture(current+(event.key==='ArrowRight'?1:-1))}}
    if(event.key==='Home'||event.key==='End'){{event.preventDefault();showCapture(event.key==='Home'?0:thumbnails.length-1)}}
  }});
  var touchStart=null;
  document.getElementById('captura').addEventListener('touchstart',function(event){{
    if(event.touches.length===1)touchStart={{x:event.touches[0].clientX,y:event.touches[0].clientY}};
  }},{{passive:true}});
  document.getElementById('captura').addEventListener('touchend',function(event){{
    if(!touchStart||!event.changedTouches.length)return;
    var dx=event.changedTouches[0].clientX-touchStart.x,dy=event.changedTouches[0].clientY-touchStart.y;touchStart=null;
    if(Math.abs(dx)>60&&Math.abs(dx)>Math.abs(dy)*1.5)showCapture(current+(dx<0?1:-1));
  }},{{passive:true}});
  // Mode fosc o clar (segueix el sistema fins que es tria)
  document.getElementById('tema').addEventListener('click',function(){{
    var fosc=root.dataset.theme?root.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme=fosc?'light':'dark';
    try{{localStorage.setItem('cm-web-tema',root.dataset.theme)}}catch(e){{}}
  }});
}})();
</script>
</body>
</html>
"""
    # Els salts a seccions són navegació de la pàgina; la resta obri una pestanya.
    def new_tab(match):
        attributes = match.group(1)
        href = re.search(r'\bhref="([^"]*)"', attributes)
        if not href or href.group(1).startswith("#"):
            return match.group(0)
        return '<a' + attributes + ' target="_blank" rel="noopener noreferrer">'
    return re.sub(r'<a\b([^>]*)>', new_tab, page)


def main():
    eixida = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "_site").resolve()
    for d in ("", "es", "img/ca", "img/es", "pdf"):
        (eixida / d).mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / "src" / "web" / "logo.png", eixida / "img" / "icona.png")
    shutil.copy(Path(__file__).with_name("web.css"), eixida / "estil.css")
    # Les tipografies de l'app (lliures, OFL), servides des de la mateixa web: sense Google Fonts
    sys.path.insert(0, str(ROOT))
    import build  # noqa: E402
    (eixida / "fonts").mkdir(exist_ok=True)
    for f in (ROOT / "src" / "web" / "fonts").iterdir():
        shutil.copy(f, eixida / "fonts" / f.name)
    (eixida / "fonts" / "fonts.css").write_text(build.fonts_css(lambda f: f), encoding="utf-8")
    for l in ("ca", "es"):
        for c in CAPTURES:
            shutil.copy(ROOT / "docs" / "imatges" / l / capture_filename(c), eixida / "img" / l / capture_filename(c))
    v = versio()
    (eixida / "index.html").write_text(pagina(T["ca"], "ca", "", v), encoding="utf-8")
    (eixida / "es" / "index.html").write_text(pagina(T["es"], "es", "../", v), encoding="utf-8")
    # L'app web (la mateixa que va dins de l'APK), a app/; prova/ era l'adreça de la v2
    build.web(eixida / "app")
    (eixida / "prova").mkdir(exist_ok=True)
    (eixida / "prova" / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=../app/">'
        '<link rel="canonical" href="../app/"><title>La Comunitat</title><a href="../app/">La Comunitat</a>\n', encoding="utf-8")
    (eixida / ".nojekyll").write_text("")
    print(f"Web generada a {eixida}")


if __name__ == "__main__":
    main()
