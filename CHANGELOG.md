# Registre de canvis

Tots els canvis rellevants de **La Comunitat** es documenten en este fitxer.

El projecte utilitza versions `MAJOR.MINOR` i etiqueta les versions publicades com `vX.Y`.

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
