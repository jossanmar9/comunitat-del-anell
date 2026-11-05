/*
 * La Comunitat — ajudant per a portar partides d'«El Señor de los Anillos:
 * El Destino de la Comunidad».
 * Copyright (C) 2026 Col·laboradors de La Comunitat
 *
 * Aquest programa és programari lliure: el podeu redistribuir i/o modificar
 * segons els termes de la Llicència Pública General de GNU publicada per la
 * Free Software Foundation, ja siga la versió 3 de la Llicència o (a la vostra
 * elecció) qualsevol versió posterior.
 *
 * Aquest programa es distribueix amb l'esperança que siga útil, però SENSE CAP
 * GARANTIA; ni tan sols la garantia implícita de COMERCIABILITAT o ADEQUACIÓ A
 * UN PROPÒSIT PARTICULAR. Vegeu la Llicència Pública General de GNU per a més
 * detalls: <https://www.gnu.org/licenses/>.
 *
 * Projecte de fans no oficial, sense relació amb Z-Man Games, Asmodee ni
 * Middle-earth Enterprises.
 */
/* ---------- Dades de referència per a identificar elements del joc; ajuda pròpia del projecte no oficial ---------- */
const CHARACTERS=[
  {id:'frodosam',name:"Frodo i Sam",start:"La Comarca",color:'#C99A2E',frodo:true,abilities:[
    ["Viatjar amb Frodo","Sempre","Quan Frodo viatja o participa en un viatge, el participant actual ha de gastar 1 Sigil o fer una tirada de cerca al destí de Frodo."],
    ["El suport d’Elrond","Preparar","1 vegada per torn, quan Frodo es prepara, si és en un refugi de la regió nombrada en la carta, obté també 1 Amistat de la reserva."],
    ["L’ajuda de Sam","Cerca","Cada vegada que es fa una tirada de cerca, pots gastar qualsevol quantitat d’Amistat per ignorar el mateix nombre de resultats dels dos tipus indicats en la carta."],
    ["Posar-se l’Anell","Cerca","Abans de fer una tirada de cerca, pots ignorar totes les tropes de l’Ombra presents. Si ho fas, perd 1 d’Esperança i mou l’Ull de Sauron a la regió de Frodo."]
  ]},
  {id:'merrypippin',name:"Merry i Pippin",start:"La Comarca",color:'#D07A2C',abilities:[
    ["Amics lleials","Acció (1 vegada per torn)","Obtín 1 Amistat de la reserva."],
    ["Distracció","En qualsevol moment (no és una acció)","Si hi ha menys de 4 natzguls a la regió de Merry i Pippin, pots gastar 1 Amistat per moure fins a 2 natzguls a la seua regió."],
    ["Canteu-nos alguna cosa!","Acció","Si Merry i Pippin són a la ubicació de Frodo, gasta 3 Amistat per guanyar 2 d’Esperança."]
  ]},
  {id:'aragorn',name:"Aragorn",start:"Turons del Vent",color:'#6A4C9C',abilities:[
    ["Forestal del Nord","Cerca","Si Aragorn és present en una tirada de cerca, pots tornar a tirar 1 dau."],
    ["Capità de l’Oest","Batalla","Si Aragorn és present en una tirada de batalla, retira fins a 2 tropes de l’Ombra de la seua ubicació per cada resultat indicat en la carta (en lloc d’1)."],
    ["Andúril","Acció (1 vegada per torn)","Si s’ha completat almenys 1 objectiu, retira 1 tropa de l’Ombra de la ubicació d’Aragorn."]
  ]},
  {id:'arwen',name:"Arwen",start:"Rivendell",color:'#7FA83A',abilities:[
    ["Estel del Vespre","Reclutar","Quan Arwen recluta en una ubicació dels elfs, no cal que gastes Amistat."],
    ["Enviar ajuda","Preparar","Quan Arwen es prepara, si un personatge és a la regió nombrada en la carta, pots moure 1 tropa elfa de la ubicació d’Arwen a la d’eixe personatge."],
    ["Consell","Comunitat","1 vegada en el teu torn, quan Arwen fa Comunitat en un refugi, no cal que la carta que dona o pren coincidisca amb la seua regió."],
    ["Partida en solitari","Preparar","1 vegada per torn, quan Arwen es prepara, no cal que la carta que descarta coincidisca amb la seua regió."]
  ]},
  {id:'boromir',name:"Boromir",start:"Minas Tirith",color:'#2D4F95',abilities:[
    ["Hereu del Senescal","Reclutar","Quan Boromir recluta en una ubicació de Gondor, no cal que gastes Amistat."],
    ["Heroi de Gondor","Capturar","Quan Boromir captura, gasta 1 Valor menys."],
    ["Temptat pel poder","Comunitat","Quan Boromir participa en l’acció de Comunitat, no pots donar cartes de Destí (i els altres no te’n poden rebre)."]
  ]},
  {id:'eomer',name:"Éomer",start:"Estemnet",color:'#8A5A2B',abilities:[
    ["Genet de Rohan","Acció (1 vegada per torn)","Quan Éomer fa accions, pot fer 1 acció addicional de Viatjar."],
    ["Mariscal de la Marca","Batalla","Si Éomer i almenys 1 tropa Rohirrim són presents en una tirada de batalla, ignora la pèrdua d’1 tropa aliada."]
  ]},
  {id:'eowyn',name:"Éowyn",start:"Edoras",color:'#B9A27A',abilities:[
    ["Donzella guerrera de Rohan","Reclutar","Quan Éowyn recluta en una ubicació de Rohan, no cal que gastes Amistat."],
    ["No soc cap home vivent!","Batalla","Si Éowyn és present en una tirada de batalla, retira del joc 1 natzgul de la seua regió per cada resultat indicat en la carta (i no perds 2 tropes aliades)."]
  ]},
  {id:'faramir',name:"Faramir",start:"Minas Tirith",color:'#3E83C4',abilities:[
    ["Emboscada","Viatjar","Quan Faramir viatja amb almenys 1 tropa aliada, pots fer una acció d’Atacar addicional al destí. Si ho fas, canvia 1 dau pel resultat indicat en la carta per cada Sigil que gastes."],
    ["Sigil","Viatjar","Quan Faramir viatja per un camí especial, gasta 1 símbol menys."],
    ["Saviesa de l’Antiga Raça","Acció (1 vegada per torn)","Roba una carta de Destí (si n’hi ha) de la pila de descarts de joc, si Faramir és en un refugi i en la regió nombrada en la carta."]
  ]},
  {id:'galadriel',name:"Galadriel",start:"Lòrien",color:'#3C6E3F',abilities:[
    ["Dama de la Llum","En qualsevol moment (no és una acció)","Mentre siga en un refugi, pot gastar 1 Sigil per robar a l’atzar 1 de les cartes d’esdeveniment que no s’han fet servir en la preparació."],
    ["Mirall de Galadriel","Acció","Mira fins a 4 cartes de dalt de la baralla de joc i torna-les a dalt en l’ordre que vulgues."],
    ["Nenya","Batalla","Si Galadriel i almenys 1 tropa elfa són presents en una tirada de batalla, pots tornar a tirar fins a 1 dau."]
  ]},
  {id:'gandalf',name:"Gandalf",start:"Tharbad",color:'#9AA0A6',abilities:[
    ["Mithrandir","Reclutar","Quan Gandalf recluta, afig fins a 2 tropes a la seua ubicació (en lloc d’1)."],
    ["Ombragrís","Viatjar","Quan Gandalf viatja a soles, pot moure’s fins a 2 ubicacions de distància. Quan ho fa, no pot fer servir camins especials."],
    ["Llum i flama","Batalla","Si Gandalf és present en una tirada de batalla, pots gastar Valor per canviar el mateix nombre de daus per qualsevol resultat que vulgues."]
  ]},
  {id:'gimli',name:"Gimli",start:"Erebor",color:'#5E6670',abilities:[
    ["Fill de Glóin","Reclutar","Quan Gimli recluta en una ubicació dels nans, no cal que gastes Amistat."],
    ["Enginy nan","Acció (1 vegada per torn)","Obtín 1 Valor de la reserva."]
  ]},
  {id:'gollum',name:"Gollum",start:"Mòria",color:'#2E2E2E',abilities:[
    ["Limitacions","Sempre","Gollum no pot Reclutar, Atacar ni Capturar, ni portar tropes aliades quan viatja."],
    ["Ens enganyen!","Sempre","Quan Gollum, Frodo o tropes aliades entren o s’afigen a una ubicació, perd 1 d’Esperança si tots tres hi són presents."],
    ["Guia","Cerca","Si Gollum és present en una tirada de cerca, tires 3 daus menys (encara es pot arribar a tirar 7 daus)."],
    ["Tafaner","Acció (1 vegada per torn)","Pren qualsevol carta de Sigil (si n’hi ha) de la pila de descarts de joc."],
    ["Astut","Preparar","Gollum es pot preparar encara que no siga en un refugi. Quan es prepara, pots moure 1 tropa de l’Ombra present a una ubicació adjacent (sense fer tirada de batalla)."]
  ]},
  {id:'legolas',name:"Legolas",start:"Regne del Bosc",color:'#86B33F',abilities:[
    ["Caminar en silenci","Acció (1 vegada per torn)","Obtín 1 Sigil de la reserva."],
    ["Tir certer","En qualsevol moment (no és una acció)","Gasta 1 Sigil per retirar 1 tropa de l’Ombra de la ubicació de Legolas o d’una ubicació adjacent, o per moure 1 natzgul de la seua regió a Mordor."],
    ["Vista aguda","Preparar","1 vegada per torn, quan Legolas es prepara, mira la primera carta de la baralla de l’Ombra."]
  ]}
];
const SUGGESTED=[['frodosam','legolas'],['merrypippin','eowyn'],['arwen','aragorn'],['gandalf','boromir'],['gimli','eomer']];
const OBJECTIVES=['Rebre la benedicció dels elfs',"«Saruman, la teua vara està trencada»",'Desafiar Sauron','Enfrontar-se al Balrog','Els perjurs compleixen el seu deure','Sotmetre Umbar','Cavalcar amb els Éored','Alliberar la ment de Théoden','Fer front als hereus de Freca',"«Mai més una donzella guerrera»",'«Ja en porte sis!»','Arwen desplega l\'estendard','Deixar al descobert les masmorres',"Portar la llum al Bosc Negre",'La redempció de Boromir','Assegurar el gual de l\'Anduin','Destronar Denethor','Infiltrar-se a Minas Morgul','Venjar Balin!','Desterrar l\'Ombra de les terres nanes','Els forestals asseguren Eriador','Els hòbbits juren lleialtat',"El cau d'Ella-Aranya"];
const OBJECTIVE_DETAILS={
  "Rebre la benedicció dels elfs":{setup:"Posa 3 tropes elfes sobre aquesta carta. No es poden fer servir fins que es complete l’objectiu.",complete:"Com a acció, un personatge que siga a Rivendell gasta 3 Amistat amb almenys 1 personatge més present.",reward:"Torna les tropes d’aquesta carta a la reserva. Cada participant que tinga almenys 1 personatge a Rivendell pot obtindre 1 Amistat. Guanya 1 d’Esperança."},
  "«Saruman, la teua vara està trencada»":{setup:"Afig 2 tropes de l’Ombra addicionals a Isengard.",complete:"Isengard és un refugi i Rohan no té tropes ni fortaleses de l’Ombra.",reward:"El participant actual pot obtindre 1 Destí de la reserva."},
  "Desafiar Sauron":{complete:"Un personatge que siga a Ithilien del Nord gasta una acció amb almenys 2 tropes Rohirrim, 2 tropes elfes i 3 tropes de Gondor presents.",reward:"Mou l’Ull de Sauron a Ithilien i totes les tropes de l’Ombra de Mordor a Udûn."},
  "Enfrontar-se al Balrog":{setup:"Cal usar Gandalf.",complete:"Gandalf gasta una acció a Mòria per tirar 3 daus. Segons el resultat de cada dau, perd 1, 2 o 3 d’Esperança o no passa res (mira la taula de la carta). Gandalf pot ignorar 1 dau per cada Destí que gaste i evitar la pèrdua d’1 d’Esperança per cada Valor que gaste.",reward:"Retira Gandalf del tauler. Quan es robe el pròxim «El cel s’enfosqueix», posa’l a Lòrien i guanya 2 d’Esperança: ara és Gandalf el Blanc. Quan Gandalf el Blanc fa servir «Llum i flama», pots gastar 1 Valor per canviar qualsevol nombre de daus pels resultats que vulgues."},
  "Els perjurs compleixen el seu deure":{setup:"Cal usar Aragorn.",special:"Una vegada per partida, Aragorn ha de viatjar en el seu torn d’Edoras a Erech. Quan ho fa, afig 2 tropes de l’Ombra a Pelargir i després mou totes les tropes de l’Ombra d’Umbar a Pelargir; i afig fins a 3 tropes de Gondor a Erech.",complete:"Aragorn ha fet eixe viatge i Gondor no té tropes ni fortaleses de l’Ombra.",reward:"Guanya 1 d’Esperança."},
  "Sotmetre Umbar":{complete:"Umbar és un refugi; o bé hi ha almenys 1 tropa aliada en cada ubicació de Haradwaith i cap tropa de l’Ombra a Haradwaith.",reward:"Mou qualsevol nombre de tropes aliades de Haradwaith a Pelargir."},
  "Cavalcar amb els Éored":{setup:"Cal usar Éomer.",special:"Quan Éomer ataca amb tropes Rohirrim presents i es retiren tropes de l’Ombra, pots posar-ne 1 en l’espai roig d’aquesta carta que coincidisca amb la seua regió (Rohan i les regions adjacents; 1 tropa per espai).",complete:"Hi ha 4 tropes de l’Ombra en aquesta carta.",reward:"Torna les tropes de l’Ombra a la reserva. Guanya 1 d’Esperança."},
  "Alliberar la ment de Théoden":{setup:"Posa 4 tropes Rohirrim sobre aquesta carta. No es poden fer servir fins que es complete l’objectiu.",complete:"Com a acció, un personatge que siga a Edoras gasta 2 Amistat i 1 Destí amb almenys 1 personatge més present.",reward:"Torna les tropes d’aquesta carta a la reserva. Afig fins a 2 tropes Rohirrim a Edoras. Guanya 1 d’Esperança."},
  "Fer front als hereus de Freca":{special:"Pots Capturar les Terres Brunes, encara que no siguen una fortalesa de l’Ombra, si gastes 3 Valor (com sempre) o 3 Amistat.",complete:"Les Terres Brunes són un refugi i hi ha almenys 2 tropes Rohirrim allí.",reward:"Pots afegir 1 tropa Rohirrim a les Terres Brunes. (Si després l’ocupen tropes de l’Ombra sense tropes aliades presents, perd 3 d’Esperança i retira la fitxa de refugi; no es converteix en fortalesa de l’Ombra.)"},
  "«Mai més una donzella guerrera»":{setup:"Cal usar Éowyn.",special:"Si Éowyn és present en una tirada de batalla, pot gastar 2 Valor per canviar 1 dau pel resultat de natzgul.",complete:"Éowyn ha destruït almenys 2 natzguls i Rohan no té tropes ni fortaleses de l’Ombra.",reward:"Guanya 1 d’Esperança."},
  "«Ja en porte sis!»":{setup:"Cal usar Legolas.",special:"Quan Legolas fa servir «Tir certer» per retirar una tropa de l’Ombra, la pot posar sobre aquesta carta (en lloc de tornar-la a la reserva).",complete:"Hi ha 6 tropes de l’Ombra en aquesta carta.",reward:"Torna les tropes de l’Ombra d’aquesta carta a la reserva. Guanya 1 d’Esperança."},
  "Arwen desplega l'estendard":{setup:"Cal usar Arwen.",complete:"Arwen gasta una acció i 1 Amistat a Minas Tirith quan hi ha almenys 1 tropa de Gondor, 1 Rohirrim, 1 elfa i 1 nana presents, i Minas Tirith és un refugi.",reward:"Guanya 1 d’Esperança."},
  "Deixar al descobert les masmorres":{setup:"Cal usar Galadriel. Afig 1 tropa de l’Ombra addicional a Dol Guldur.",special:"Galadriel pot Capturar Dol Guldur si gasta 3 Valor (com sempre) o 2 Destí i 1 Valor.",complete:"Dol Guldur és un refugi i hi ha almenys 3 tropes elfes a Dol Guldur.",reward:"Si Galadriel és a Dol Guldur, guanya 1 d’Esperança addicional (a banda dels 2 que es guanyen en Capturar Dol Guldur)."},
  "Portar la llum al Bosc Negre":{setup:"Posa 1 tropa de l’Ombra al Camí del Bosc Vell i 1 al Bosc Negre Sud.",complete:"El Bosc Negre no té tropes de l’Ombra (no cal Capturar Dol Guldur) i hi ha almenys 1 tropa elfa en cada ubicació del Bosc Negre.",reward:"Tria una ubicació del Bosc Negre i mou-hi qualsevol nombre de tropes elfes del Bosc Negre. Guanya 1 d’Esperança."},
  "La redempció de Boromir":{setup:"Cal usar Boromir.",complete:"Boromir i almenys 1 personatge més són en una ubicació on es retira l’última tropa aliada en una batalla.",reward:"Retira fins a 2 tropes de l’Ombra de la ubicació de Boromir. Després retira la figura de Boromir del tauler: ja no pot fer accions. Quan es complete el pròxim objectiu, roba a l’atzar 1 carta de personatge de la caixa per substituir Boromir i posa’n la figura a la seua ubicació inicial."},
  "Assegurar el gual de l'Anduin":{setup:"Cal usar Faramir. Posa 1 tropa de l’Ombra a Osgiliath.",special:"Faramir pot Capturar Osgiliath, encara que no siga una fortalesa de l’Ombra, si gasta 3 Valor (com sempre) o 2 Destí i 1 Sigil.",complete:"Osgiliath és un refugi.",reward:"Pots afegir 1 tropa de Gondor a Osgiliath. (Si després l’ocupen tropes de l’Ombra sense tropes aliades presents, perd 3 d’Esperança i retira la fitxa de refugi; no es converteix en fortalesa de l’Ombra.)"},
  "Destronar Denethor":{setup:"Posa 4 tropes de Gondor sobre aquesta carta. No es poden fer servir fins que es complete l’objectiu.",complete:"Com a acció, un personatge que siga a Minas Tirith gasta 2 Sigil, 1 Amistat i 1 Valor amb almenys 1 personatge més present.",reward:"Torna les tropes d’aquesta carta a la reserva. Afig fins a 3 tropes de Gondor a Minas Tirith. Guanya 1 d’Esperança."},
  "Infiltrar-se a Minas Morgul":{setup:"Afig 1 tropa de l’Ombra addicional a Minas Morgul.",special:"Pots Capturar Minas Morgul si gastes 3 Valor (com sempre) o 3 Sigil.",complete:"Minas Morgul és un refugi.",reward:"El participant actual pot obtindre 2 Sigil. Mira les 2 primeres cartes de l’Ombra: pots retirar-ne 1 o les 2 de la partida i tornar la resta a dalt de la baralla de l’Ombra en l’ordre que vulgues."},
  "Venjar Balin!":{complete:"Mòria és un refugi i hi ha almenys 2 tropes nanes a Mòria.",reward:"Mou a Mòria qualsevol nombre de tropes nanes d’altres ubicacions. Si ara n’hi ha almenys 4, el participant actual pot obtindre 2 Valor."},
  "Desterrar l'Ombra de les terres nanes":{setup:"Cal usar Gimli. Posa 1 tropa de l’Ombra a Ered Luin.",complete:"No hi ha tropes de l’Ombra a Ered Luin, hi ha almenys 4 tropes nanes allí, i a la Vall no hi ha tropes ni fortaleses de l’Ombra.",reward:"El participant actual pot obtindre 2 Valor. Guanya 1 d’Esperança."},
  "Els forestals asseguren Eriador":{complete:"Eriador no té tropes ni fortaleses de l’Ombra i hi ha almenys 1 tropa aliada en cada ubicació d’Eriador.",reward:"Mou qualsevol nombre de tropes aliades d’Eriador als Turons del Vent i/o a Tharbad. Guanya 1 d’Esperança."},
  "Els hòbbits juren lleialtat":{setup:"Cal usar Merry i Pippin.",special:"Mentre siguen en un refugi, Merry i Pippin poden gastar una acció per descartar 1 carta d’Amistat que coincidisca amb la seua regió i posar 1 Amistat de la reserva en el símbol de refugi corresponent de la carta (elfs, nans, Rohan o Gondor).",complete:"Hi ha 1 Amistat en 2 dels símbols de refugi de la carta.",reward:"Dona les 2 Amistat de la carta a Merry i Pippin. Guanya 1 d’Esperança."},
  "El cau d'Ella-Aranya":{setup:"Cal usar Gollum. A més, qui porta Frodo no pot portar també Gollum.",complete:"Sam gasta una acció a Minas Morgul amb Gollum present per tirar 3 daus. Segons el resultat de cada dau, perd 1, 2 o 3 d’Esperança o no passa res (mira la taula de la carta). Perd també 1 d’Esperança per cada Destí (carta o fitxa) del participant de Gollum; en solitari, per cada carta de Destí de la teua mà. Sam pot ignorar 1 dau per cada Valor que gaste i evitar la pèrdua d’1 d’Esperança per cada Amistat que gaste.",reward:"Si Frodo no ha perdut gens d’Esperança per aquesta carta, pot fer 1 acció addicional aquest torn."},
  "Destruir l'Anell Únic":{setup:"Cal usar Frodo i Sam.",special:"Has de completar tots els altres objectius abans d’aquest.",complete:"Com a acció, Frodo gasta 5 Destí a la Muntanya del Destí i després sobreviu a una última tirada de cerca, a la qual se suma 1 dau per cada punt d’Esperança perdut (fins a 7 daus). Per exemple, si només queden 3 d’Esperança, tira 5 daus de cerca addicionals.",reward:"Sauron és derrotat i tots guanyeu la partida!"}
};
// Noms d'objectius de versions anteriors (les partides guardades els porten dins)
const OBJ_ANTICS={"«Saruman, el teu bastó està trencat»":"«Saruman, la teua vara està trencada»","Mai més una donzella guerrera":"«Mai més una donzella guerrera»","Portar la llum al Bosc Fosc":"Portar la llum al Bosc Negre","El cau de l'Aranya":"El cau d'Ella-Aranya"};
const RING_OBJ='Destruir l\'Anell Únic';
const SCENARIOS=[
  {name:'La primera partida',level:['intro','estandard'],obj:[0,1,2]},
  {name:'Mantingueu a ratlla la foscor',level:['intro','estandard'],obj:[3,4,5]},
  {name:'Genets de Rohan',level:['heroica','epica'],obj:[6,7,8,9]},
  {name:'El destí dels elfs',level:['heroica','epica'],obj:[10,11,12,13]},
  {name:'Fills del senescal',level:['heroica','epica'],obj:[14,15,16,17]},
  {name:'No hi ha heroi petit',level:['llegendaria'],obj:[18,19,20,21,22]}
];
const LEVELS={intro:{name:'Introductòria',skies:4,obj:4},estandard:{name:'Estàndard',skies:5,obj:4},heroica:{name:'Heroica',skies:5,obj:5},epica:{name:'Èpica',skies:6,obj:5},llegendaria:{name:'Llegendària',skies:6,obj:6}};
const EVENTS_BY_PLAYERS={1:5,2:6,3:6,4:7,5:9};
const HAND_BY_PLAYERS={1:4,2:4,3:3,4:2,5:2};
const HOPE_START=6,HOPE_MAX=8,THREAT=[2,2,3,3,4,4,5];
const SETUP_STEPS=[
  ['Tauler','Posa el tauler al centre de la taula.'],
  ['Marcadors','Amenaça i esperança a la casella amb punt del seu indicador (l\'esperança, a la 6).'],
  ['Baralla d\'Ombra','Les 2 cartes especials (Sauron i Saruman) a la pila de descarts d\'Ombra; barreja la resta i fes la baralla.'],
  ['Tropes aliades','Nans: Ered Luin, Erebor, Turons de Ferro. Elfs: Ports Grisos, Rivendell, Lòrien, Regne del Bosc. Rohirrim: Abisme de Helm, Edoras, Estemnet. Gondor: 2 a Minas Tirith, 2 a Dol Amroth, 1 a Pelargir.'],
  ['Tropes de l\'Ombra','1 Terres Brunes, 1 Isengard, 2 Mòria, 1 Dol Guldur, 3 Rhûn, 2 Minas Morgul, 2 Barad-dûr, 3 Núrn, 1 Umbar, 2 Harad Pròxim. Després roba 9 cartes d\'Ombra i posa 1 tropa al lloc roig de cada una; descarta-les.'],
  ['Natzguls i Ull','Natzguls: 2 Eriador, 1 Rhudaur, 1 Muntanyes Boiroses, 1 Gondor, 4 Mordor. L\'Ull de Sauron a Eriador.'],
  ['Objectius','Destruir l\'Anell Únic i la resta d\'objectius triats, bocamunt. Segueix les seues instruccions de preparació.'],
  ['Personatges','Cada participant pren les seues 2 cartes de personatge i referència, i posa les figures al lloc d\'inici.'],
  ['Cartes de joc','Separa El cel s\'enfosqueix; afegeix els esdeveniments a les 48 de regió, barreja i reparteix la mà inicial. Fes els muntons segons la dificultat, 1 cel enfosquit a cada un, i apila\'ls.'],
  ['Primer torn','Comença qui tinga la carta de regió amb el número més baix (o qui porte Frodo, si és la primera partida).']
];
