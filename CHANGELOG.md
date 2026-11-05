# Registre de canvis

Tots els canvis rellevants de **La Comunitat** es documenten en este fitxer.

El projecte utilitza versions `MAJOR.MINOR.PATCH` i etiqueta les versions publicades com `vX.Y.Z`.

## [3.0.2] - 2026-11-05

### Corregit
- Textos de les cartes de personatge i d'objectiu revisats un a un amb les cartes del joc, en valencià i en castellà. Els errors més importants:
  - Frodo i Sam: faltaven la regla de viatjar (gastar 1 Sigil o fer una cerca) i «Posar-se l'Anell».
  - Merry i Pippin: «Distracció» compta natzguls, no tropes de l'Ombra.
  - Arwen, Boromir i Éowyn recluten sense gastar Amistat en qualsevol ubicació dels elfs, de Gondor o de Rohan, no només en una ciutat.
  - Boromir: «Temptat pel poder» prohibeix donar cartes de Destí.
  - Éomer: «Mariscal de la Marca» ignora la pèrdua d'una tropa aliada qualsevol.
  - Legolas: «Tir certer» (abans «Tir segur») mou un natzgul, no una tropa.
  - Gollum: faltaven les limitacions i «Ens enganyen!»; «Tafaner» pren cartes de Sigil.
  - «Saruman, el teu bastó està trencat» dona 1 Destí (no Resistència), i «Infiltrar-se a Minas Morgul» no obliga a usar Faramir.
  - Els objectius amb tirada («Enfrontar-se al Balrog», «El cau de l'Aranya») expliquen la tirada, i els de Capturar diuen el cost alternatiu exacte.
- Quatre objectius tenen ara un nom en valencià més fidel a la carta: «Saruman, la teua vara està trencada», «Mai més una donzella guerrera», «Portar la llum al Bosc Negre» i «El cau d'Ella-Aranya». Les partides guardades amb els noms antics s'actualitzen soles en obrir-les.
- La fitxa de les espases es diu «Valor» en valencià i en castellà (abans «Heroicidad» en algunes pantalles en castellà); el Bosc Fosc ara és el Bosc Negre, com al mapa.
- Noms de les habilitats com en les cartes en castellà (Montaraz del Norte, Sombragris, Ingenio enano, ¡Cantaos algo!…) i Éomer comença a Estemnet.

## [3.0.1] - 2026-11-02

### Afegit
- Pàgina de privacitat a la web, en valencià i castellà: l'app no recull cap dada.
- Botó «Navegador» a la web, que obri l'app web. És el que es destaca a l'iPhone, l'iPad, el Mac i els Chromebook.

### Canviat
- Els botons de Windows, Linux i Android de la web baixen directament el fitxer de l'última versió.
- Els fitxers de cada versió ja no porten el número al nom: `LaComunitat-installador.exe`, `LaComunitat-windows-portable.zip`, `comunitat-del-anell.deb`, `LaComunitat-linux.tar.gz` i `LaComunitat-android.apk`.
- Sense cap partida oberta, la capçalera ja no mostra el camp buit del nom.

### Corregit
- Al mòbil, el menú de la web es tallava i no es veien l'idioma ni el tema.
- Dos enllaços de l'índex del README no portaven enlloc.

## [3.0.0] - 2026-10-30

Una sola persona porta la partida, i ara també des del mòbil: La Comunitat funciona igual a Windows, a Linux, a Android i al navegador.

### Afegit
- **App per a Android** (`.apk` a cada versió publicada), feta amb Capacitor a partir de la mateixa app. Exportar una partida obri el menú «Compartir» d'Android; el botó «enrere» tanca les finestres.
- **App web instal·lable** a la web del projecte (`/app/`): funciona sense connexió i es pot afegir a la pantalla d'inici. Les partides es guarden al navegador.
- **Canviar el mapa** des de l'app: tria una imatge i es guarda per a totes les partides (abans calia copiar `mapa.jpg` a la carpeta de dades).
- Botó «Fer una còpia ara» a les còpies de seguretat.
- A l'ordinador, les partides exportades es guarden a Baixades sense sobreescriure res.
- Proves de l'app en un navegador de veritat (versió d'escriptori i web), del magatzem i del pas de la v2 a la v3.

### Canviat
- La partida, l'historial i les còpies es porten des de l'app mateixa (`src/web/magatzem.js`); el programa d'escriptori només guarda els fitxers. Els fitxers continuen sent els mateixos (`partides/`, `copies/`, `historial.json`).
- El programa d'escriptori només accepta connexions del mateix ordinador.
- Al mòbil, les pistes van en dues columnes.
- Les compilacions donen sempre el mateix `comunitat.py`.

### Llevat
- **El mode de taula connectada**: la sala, els jugadors amb PIN, les sessions, el QR i l'entrada des d'altres mòbils. Ara una persona porta la partida i la resta juga al tauler.
- Les races i els àlies dels jugadors.
- La base de dades SQLite de la v2.7: en obrir la v3 per primera vegada, si tenia canvis sense passar als fitxers JSON s'hi passen, i es guarda a `copies/v2/`.

## [2.7.0] - 2026-10-27

- Guardat transaccional conjunt de l’estat actiu (partida, jugadors, sessions i historial) en SQLite, mantenint JSON compatibles.
- Recuperació de projeccions JSON parcials, còpia coherent de SQLite abans de cada inici i bloqueig de doble instància sobre les mateixes dades.
- Errors d’escriptura amb rollback de memòria; dades corruptes preservades en lloc de sobreescriure-les amb un estat buit.
- Persistència i identitats separades en mòduls, incrustats en el programa distribuït.
- Proves de disc ple, transacció interrompuda, corrupció, migració, còpies, sessions i recuperació.
- Web amb enllaç al CHANGELOG i captures actuals, galeria amb fletxes, teclat, miniatures i gestos mòbils en VAL/CAS. Enllaços a pàgines, documents i descàrregues en pestanya nova.

## [2.6.0] - 2026-10-27

- Etiqueta de raça «Humà» / «Humano», mantenint el codi intern compatible amb els guardats.
- Proposta local d’àlies masculí/femení segons el nom, selector de correcció i opció neutra; pools inventats diferenciats per raça, preferència guardada sense alterar PIN ni sessions.

- Inici sense partida carregada, alta automàtica de jugadors en crear-la amb noms i races, i recuperació de la sala en obrir guardats; identitats i PIN existents es reutilitzen.

- Sala de partida amb alta, edició i eliminació de jugadors pel màster local.
- UID estable, noms únics normalitzats, àlies inventats per raça i canvi d’àlies controlat pel màster.
- PIN de quatre dígits amb salt i PBKDF2-HMAC-SHA256; visualització única i límit d’intents per IP.
- Una sessió revocable per jugador, reconnexió amb token, desvinculació i bloqueig de noves vinculacions.
- Entrada mòbil amb QR comú → jugador → PIN; espera fins que es prepare la partida.
- Separació d’administració local i jugades cooperatives; identitats protegides d’escriptures genèriques.
- Migració de jugadors antics, conservació de guardats i revocació de sessions v2.5 sense autenticació.
- Interfície VAL/CAS, manuals, web i avisos de projecte no oficial actualitzats; proves de sala i compatibilitat.

## [2.5.0] - 2026-10-26

### Afegit
- Perfils de jugador editables des de la mateixa partida.
- Elecció de raça per a l'àlies: Home, Elf, Nan o Hòbbit.
- Generació automàtica d'un àlies de fantasia segons la raça seleccionada.
- Opció per generar un nou àlies des del perfil.
- Visualització del nom i l'àlies del jugador a la capçalera.

### Millorat
- Els jugadors poden corregir o canviar el seu nom sense abandonar la partida.
- El canvi de raça genera automàticament un nou àlies.
- Els noms, la raça i l'àlies es conserven entre sessions.
- Compatibilitat amb les dades de jugador creades amb versions anteriors.

### Corregit
- No es permet que dos jugadors utilitzen el mateix nom.
- La comprovació de noms duplicats ignora majúscules, minúscules, accents i espais sobrants.
- S'evita l'assignació del mateix àlies a dos jugadors.

## 2.4.2 — Correcció responsive

- Corregida la disposició de l’aplicació en mòbil i tauleta.
- El panell del torn i el contingut principal tornen a ocupar tota l’amplària disponible.
- Millorada la disposició dels marcadors i de la capçalera en pantalles estretes.

## [2.4] - 2026-10-26

### Canviat
- Renovació visual completa de la interfície de l’app, amb una capçalera més compacta, navegació en forma de selector, marcadors més clars i una jerarquia visual més marcada.
- Panells, mapa, torn, botons, modals, personatges i objectius adopten un estil més coherent amb la identitat de La Comunitat.
- Millora de l’adaptació a pantalles menudes i de la distribució de la barra lateral del torn.
- Renovació de la web pública amb una portada més visual, millor presentació de les captures, targetes de característiques i crides a l’acció més clares.
- Es manté l’estètica de pergamí i Terra Mitjana, però amb un acabat més net i modern.

## [2.3] - 2026-10-26

### Afegit
- Fitxes de referència dels 13 personatges, accessibles des de la pestanya **Comunitat** i des del torn.
- Fitxes dels 24 objectius amb preparació, regles especials, condicions i efectes en completar-los.
- Botons d'informació als objectius de la partida.
- Avís a les fitxes de referència perquè, davant qualsevol discrepància, prevalga la carta física del joc.
- Este `CHANGELOG.md`.

### Millorat
- Poliment visual de panells, fitxes, modals i elements interactius mantenint l'estètica de pergamí i Terra Mitjana.
- Presentació dels personatges en la pestanya **Comunitat**.
- Adaptació de les noves fitxes a pantalles mòbils.
- Traduccions de la interfície nova al castellà; els textos de referència que encara no tenen traducció específica conserven el valencià en lloc d'inventar una traducció.

## [2.2] - 2026

### Afegit
- Paperera de partides amb recuperació segura.
- Proves de navegador amb dues sessions.
- Validació més estricta de les partides importades.

### Millorat
- Guardat fiable en disc i sincronització entre diversos dispositius.
- Control de revisions per evitar sobreescriure canvis simultanis.
- Reintents de guardat sense duplicar jugades.
- Persistència coordinada de partida, registre i passos per desfer.

## [2.1] - 2026

### Afegit
- Finestra pròpia de l'aplicació.
- Còpies de seguretat de les partides.
- Exportació i importació de partides.
- Eines per gestionar la carpeta de dades.

## [2.0] - 2026

### Afegit
- Paquets d'instal·lació per a Windows i Linux.
- Manuals i documentació d'instal·lació.
- Web del projecte i versió de prova al navegador.

### Canviat
- Reorganització del projecte en `src/`, `docs/`, `paquets/`, `eines/` i `tests/`.

## [1.5] - 2026

### Afegit
- Retrats dels personatges a la preparació, el torn i l'historial.

## [1.4] - 2026

### Afegit
- Invitació a la partida mitjançant codi QR.
- Resum de final de partida i historial de resultats.
- Mode fosc.
- Executable per a Windows.

## [1.x] - 2026

### Afegit
- Primera versió funcional de l'ajudant de partida.
- Interfície en valencià i castellà.
- Seguiment d'Esperança, Amenaça, torns, cerques i batalles.
- Preparació de la partida, personatges, objectius i mapa de la Terra Mitjana.

> Les entrades anteriors a la 2.2 s'han reconstruït a partir de la documentació i l'evolució conservada al repositori; no pretenen ser un llistat exhaustiu de cada commit.
