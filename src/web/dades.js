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
  {id:'frodosam',name:'Frodo i Sam',start:'La Comarca',color:'#C99A2E',frodo:true,abilities:[
    ['El suport d’Elrond','Preparar','Una vegada per torn: si són en un refugi de la regió de la carta, poden obtindre 1 Amistat.'],
    ['L’ajuda de Sam','Cerca','Gasta fitxes per ignorar el mateix nombre de resultats de la tirada de cerca.']
  ]},
  {id:'merrypippin',name:'Merry i Pippin',start:'La Comarca',color:'#D07A2C',abilities:[
    ['Amic lleial','Acció','Una vegada per torn: obtín 1 Amistat.'],
    ['Distracció','Qualsevol torn','Si hi ha menys de 4 tropes de l’Ombra a la regió, gasta 1 Amistat per moure-hi fins a 2 natzguls.'],
    ['Canteu-nos una cançó!','Acció','Si són al lloc de Frodo, gasta 3 Amistat per guanyar 2 d’Esperança.']
  ]},
  {id:'aragorn',name:'Aragorn',start:'Turons del Vent',color:'#6A4C9C',abilities:[
    ['Explorador del Nord','Cerca','Pot repetir 1 dau de cerca.'],
    ['Capità de l’Oest','Batalla','Retira 2 tropes de l’Ombra per cada resultat indicat a la seua carta.'],
    ['Andúril','Acció','Una vegada per torn, després d’haver completat almenys 1 objectiu: retira 1 tropa de l’Ombra.']
  ]},
  {id:'arwen',name:'Arwen',start:'Rivendell',color:'#7FA83A',abilities:[
    ['Estel del Vespre','Reclutar a Minas Tirith','No gasta Amistat.'],
    ['Enviar ajuda','Preparar','Si un personatge és a la regió de la carta, mou 1 tropa elfa d’Arwen fins a eixe personatge.'],
    ['Donar consell','Comunitat · refugi','Una vegada per torn: no cal que la carta coincidisca amb la regió.']
  ]},
  {id:'boromir',name:'Boromir',start:'Minas Tirith',color:'#2D4F95',abilities:[
    ['Hereu del Senescal','Reclutar a Minas Tirith','No gasta Amistat.'],
    ['Heroi de Gondor','Capturar','Gasta 1 Valor menys.'],
    ['Temptat pel poder','Comunitat','No pot donar ni prendre cartes amb l’acció de Comunitat.']
  ]},
  {id:'eomer',name:'Éomer',start:'Eastemnet',color:'#8A5A2B',abilities:[
    ['Genet de Rohan','Acció','Una vegada per torn: obtín 1 acció de Viatjar addicional.'],
    ['Mariscal de la Marca','Batalla','Si hi ha Rohirrim presents, ignora la pèrdua d’1 tropa Rohirrim.']
  ]},
  {id:'eowyn',name:'Éowyn',start:'Edoras',color:'#B9A27A',abilities:[
    ['Donzella de l’escut de Rohan','Reclutar a Edoras','No gasta Amistat.'],
    ['No soc cap home vivent','Batalla','Pot retirar natzguls amb els resultats indicats a la carta, sense retirar la tropa aliada associada.']
  ]},
  {id:'faramir',name:'Faramir',start:'Minas Tirith',color:'#3E83C4',abilities:[
    ['Emboscada','Viatjar','Si viatja amb tropes de Gondor, obté un atac addicional al lloc de destí; pot gastar fitxes per modificar resultats de batalla segons la carta.'],
    ['Sigil·lós','Viatjar','Gasta 1 símbol menys en els camins especials.'],
    ['Saviesa dels Eldar','Acció','Una vegada per torn, si és en un refugi: recupera de la pila de descart una carta que coincidisca amb la regió.']
  ]},
  {id:'galadriel',name:'Galadriel',start:'Lòrien',color:'#3C6E3F',abilities:[
    ['Dama de la Llum','Qualsevol torn','En un refugi, gasta 1 fitxa indicada per robar a l’atzar un esdeveniment no utilitzat.'],
    ['Mirall de Galadriel','Acció','Mira fins a 4 cartes superiors de la baralla de joc i torna-les a ordenar.'],
    ['Nenya','Batalla','Si hi ha una tropa elfa present, repeteix 1 dau de batalla.']
  ]},
  {id:'gandalf',name:'Gandalf',start:'Tharbad',color:'#9AA0A6',abilities:[
    ['Mithrandir','Reclutar','Recluta 1 tropa addicional.'],
    ['Shadowfax','Viatjar','Si viatja a soles, pot moure 2 llocs; no pot usar-ho en camins especials.'],
    ['Llum i flama','Batalla','Pot gastar fitxes per modificar resultats de batalla segons la carta.']
  ]},
  {id:'gimli',name:'Gimli',start:'Erebor',color:'#5E6670',abilities:[
    ['Fill de Glóin','Reclutar en un lloc nan','No gasta Amistat.'],
    ['Artesania nana','Acció','Una vegada per torn: obtín 1 Valor.']
  ]},
  {id:'gollum',name:'Gollum',start:'Mòria',color:'#2E2E2E',abilities:[
    ['Guia','Cerca','Tira 3 daus de cerca menys. No pot Reclutar, Atacar ni Capturar.'],
    ['Escorredís','Acció','Una vegada per torn: pren una carta permesa de la pila de descart.'],
    ['Astut','Preparar','Pot preparar-se sense haver de ser en un refugi i aplica el moviment indicat a la seua carta.']
  ]},
  {id:'legolas',name:'Legolas',start:'Regne del Bosc',color:'#86B33F',abilities:[
    ['Caminar en silenci','Acció','Una vegada per torn: obtín 1 Sigil.'],
    ['Tir segur','Qualsevol torn','Gasta 1 Sigil per retirar 1 tropa de l’Ombra d’un lloc adjacent o moure 1 tropa de l’Ombra de la regió a Mordor.'],
    ['Vista aguda','Preparar','Una vegada per torn: mira la carta superior de la baralla de l’Ombra.']
  ]}
];
const SUGGESTED=[['frodosam','legolas'],['merrypippin','eowyn'],['arwen','aragorn'],['gandalf','boromir'],['gimli','eomer']];
const OBJECTIVES=['Rebre la benedicció dels elfs','«Saruman, el teu bastó està trencat»','Desafiar Sauron','Enfrontar-se al Balrog','Els perjurs compleixen el seu deure','Sotmetre Umbar','Cavalcar amb els Éored','Alliberar la ment de Théoden','Fer front als hereus de Freca','Mai més una donzella guerrera','«Ja en porte sis!»','Arwen desplega l\'estendard','Deixar al descobert les masmorres','Portar la llum al Bosc Fosc','La redempció de Boromir','Assegurar el gual de l\'Anduin','Destronar Denethor','Infiltrar-se a Minas Morgul','Venjar Balin!','Desterrar l\'Ombra de les terres nanes','Els forestals asseguren Eriador','Els hòbbits juren lleialtat','El cau de l\'Aranya'];
const OBJECTIVE_DETAILS={
  'Rebre la benedicció dels elfs':{setup:'Reserva 3 tropes elfiques sobre la carta; no es poden usar fins a completar-la.',complete:'Un personatge a Rivendell gasta una acció i 3 Amistat mentre hi haja almenys un altre personatge allí.',reward:'Torna les tropes a la reserva. Cada participant amb un personatge a Rivendell pot obtindre 1 Amistat. Guanya 1 d’Esperança.'},
  '«Saruman, el teu bastó està trencat»':{setup:'Afig 2 tropes de l’Ombra addicionals a Isengard.',complete:'Isengard és un refugi i Rohan no té tropes ni fortaleses de l’Ombra.',reward:'El participant actual pot obtindre 1 Resistència.'},
  'Desafiar Sauron':{complete:'Un personatge gasta una acció a Ithilien del Nord amb almenys 2 Rohirrim, 2 tropes elfiques i 3 de Gondor presents.',reward:'Mou l’Ull de Sauron a Ithilien i totes les tropes de l’Ombra de Mordor a Udûn.'},
  'Enfrontar-se al Balrog':{setup:'Cal usar Gandalf.',complete:'Gandalf gasta una acció a Mòria i resol la prova indicada a la carta; pot gastar les fitxes permeses per mitigar-ne els resultats.',reward:'Retira Gandalf. Quan aparega el següent «El cel s’enfosqueix», torna’l a Lòrien com Gandalf el Blanc i guanya 2 d’Esperança.'},
  'Els perjurs compleixen el seu deure':{setup:'Cal usar Aragorn.',complete:'Aragorn ha viatjat d’Edoras a Erech segons la preparació de la carta, i Gondor queda lliure de tropes i fortaleses de l’Ombra.',reward:'Guanya 1 d’Esperança.'},
  'Sotmetre Umbar':{complete:'Umbar és un refugi; o bé hi ha almenys 1 tropa aliada en cada lloc de Haradwaith i cap tropa de l’Ombra a la regió.',reward:'Pots moure qualsevol nombre de tropes aliades de Haradwaith a Pelargir.'},
  'Cavalcar amb els Éored':{setup:'Cal usar Éomer.',complete:'Reuneix 4 tropes de l’Ombra sobre la carta mitjançant els atacs d’Éomer amb Rohirrim, respectant els espais de regió de la carta.',reward:'Torna les 4 tropes a la reserva i guanya 1 d’Esperança.'},
  'Alliberar la ment de Théoden':{setup:'Reserva 4 tropes Rohirrim sobre la carta.',complete:'Un personatge a Edoras gasta una acció i les fitxes indicades a la carta mentre hi haja almenys un altre personatge allí.',reward:'Torna les tropes a la reserva, afig fins a 2 Rohirrim a Edoras i guanya 1 d’Esperança.'},
  'Fer front als hereus de Freca':{special:'Es pot Capturar Dunland encara que no siga una fortalesa de l’Ombra, pagant el cost alternatiu indicat a la carta.',complete:'Dunland és un refugi i hi ha almenys 2 tropes Rohirrim allí.',reward:'Pots afegir 1 Rohirrim a Dunland. Si després cau en mans de l’Ombra, perd 3 d’Esperança i retira el refugi.'},
  'Mai més una donzella guerrera':{setup:'Cal usar Éowyn.',complete:'Éowyn ha destruït almenys 2 natzguls i Rohan està lliure de tropes i fortaleses de l’Ombra.',reward:'Guanya 1 d’Esperança.'},
  '«Ja en porte sis!»':{setup:'Cal usar Legolas.',complete:'Quan «Tir segur» retire una tropa de l’Ombra, pots posar-la sobre la carta. Completa-la en arribar a 6.',reward:'Torna les 6 tropes a la reserva i guanya 1 d’Esperança.'},
  "Arwen desplega l'estendard":{setup:'Cal usar Arwen.',complete:'Arwen gasta una acció i 1 Amistat a Minas Tirith quan és un refugi i hi ha almenys 1 tropa de Gondor, Rohirrim, elfa i nana.',reward:'Guanya 1 d’Esperança.'},
  'Deixar al descobert les masmorres':{setup:'Cal usar Galadriel. Afig 1 tropa de l’Ombra addicional a Dol Guldur.',special:'Galadriel disposa del cost alternatiu de Captura indicat a la carta.',complete:'Dol Guldur és un refugi i hi ha almenys 3 tropes elfiques allí.',reward:'Si Galadriel és a Dol Guldur, guanya 1 d’Esperança addicional.'},
  'Portar la llum al Bosc Fosc':{setup:'Posa 1 tropa de l’Ombra al Camí del Bosc Vell i 1 al Bosc Fosc Meridional.',complete:'El Bosc Fosc no té tropes de l’Ombra i hi ha almenys 1 tropa elfa en cada lloc de la regió. No cal capturar Dol Guldur.',reward:'Tria un lloc del Bosc Fosc i mou allí qualsevol nombre de tropes elfiques de la regió. Guanya 1 d’Esperança.'},
  'La redempció de Boromir':{setup:'Cal usar Boromir.',complete:'Boromir i almenys un altre personatge són al lloc on es retira l’última tropa aliada durant una batalla.',reward:'Retira fins a 2 tropes de l’Ombra del lloc de Boromir i després retira Boromir. En completar el següent objectiu, substitueix-lo per un personatge aleatori no utilitzat.'},
  "Assegurar el gual de l'Anduin":{setup:'Cal usar Faramir. Posa 1 tropa de l’Ombra a Osgiliath.',special:'Faramir pot Capturar Osgiliath amb el cost normal o amb el cost alternatiu indicat a la carta.',complete:'Osgiliath és un refugi.',reward:'Pots afegir 1 tropa de Gondor a Osgiliath. Si després cau en mans de l’Ombra, perd 3 d’Esperança i retira el refugi.'},
  'Destronar Denethor':{setup:'Reserva 4 tropes de Gondor sobre la carta.',complete:'Un personatge a Minas Tirith gasta una acció i les fitxes indicades a la carta mentre hi haja almenys un altre personatge allí.',reward:'Torna les tropes a la reserva, afig fins a 3 tropes de Gondor a Minas Tirith i guanya 1 d’Esperança.'},
  'Infiltrar-se a Minas Morgul':{setup:'Cal usar Faramir. Posa 1 tropa de l’Ombra a Minas Morgul.',special:'Faramir pot Capturar Minas Morgul amb el cost normal o amb el cost alternatiu indicat a la carta.',complete:'Minas Morgul és un refugi.',reward:'El participant actual pot obtindre 2 Sigil. Mira les 2 cartes superiors de l’Ombra: pots retirar-ne una o les dues i torna la resta al damunt en l’ordre que vulgues.'},
  'Venjar Balin!':{complete:'Mòria és un refugi i hi ha almenys 2 tropes nanes a Mòria.',reward:'Mou a Mòria qualsevol nombre de tropes nanes d’altres llocs. Si ara n’hi ha almenys 4, el participant actual pot obtindre 2 Valor.'},
  "Desterrar l'Ombra de les terres nanes":{setup:'Cal usar Gimli. Posa 1 tropa de l’Ombra a Ered Luin.',complete:'Ered Luin no té tropes de l’Ombra i hi ha almenys 4 tropes nanes allí; Dale no té tropes ni fortaleses de l’Ombra.',reward:'El participant actual pot obtindre 2 Valor. Guanya 1 d’Esperança.'},
  'Els forestals asseguren Eriador':{complete:'Eriador està lliure de tropes i fortaleses de l’Ombra i hi ha almenys 1 tropa aliada en cada lloc.',reward:'Mou qualsevol nombre de tropes aliades d’Eriador als Turons del Vent i/o Tharbad. Guanya 1 d’Esperança.'},
  'Els hòbbits juren lleialtat':{setup:'Cal usar Merry i Pippin.',special:'En un refugi poden gastar una acció i descartar una carta de la regió per posar 1 Amistat sobre el símbol de refugi corresponent de la carta.',complete:'Hi ha Amistat sobre 2 símbols de refugi de la carta.',reward:'Dona les 2 Amistat de la carta a Merry i Pippin i guanya 1 d’Esperança.'},
  "El cau de l'Aranya":{setup:'Cal usar Gollum; qui porta Frodo i Sam no pot portar també Gollum.',complete:'Sam gasta una acció a Minas Morgul amb Gollum present i resol la prova indicada a la carta; les fitxes permeses poden mitigar-ne els resultats.',reward:'Si Frodo no ha perdut Esperança durant la prova, pot fer 1 acció addicional este torn.'},
  "Destruir l'Anell Únic":{special:'Tots els altres objectius han d’estar completats.',complete:'Frodo i Sam són a la Muntanya del Destí, gasten 5 de Destí i sobreviuen a la cerca final. Afig 1 dau per cada punt d’Esperança que falte, fins a un màxim de 7 daus.',reward:'Sauron és derrotat: la Comunitat guanya la partida.'}
};
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
  ['Tropes aliades','Nans: Ered Luin, Erebor, Turons de Ferro. Elfs: Ports Grisos, Rivendell, Lòrien, Regne del Bosc. Rohirrim: Abisme de Helm, Edoras, Eastemnet. Gondor: 2 a Minas Tirith, 2 a Dol Amroth, 1 a Pelargir.'],
  ['Tropes de l\'Ombra','1 Terres Brunes, 1 Isengard, 2 Mòria, 1 Dol Guldur, 3 Rhûn, 2 Minas Morgul, 2 Barad-dûr, 3 Núrn, 1 Umbar, 2 Harad Pròxim. Després roba 9 cartes d\'Ombra i posa 1 tropa al lloc roig de cada una; descarta-les.'],
  ['Natzguls i Ull','Natzguls: 2 Eriador, 1 Rhudaur, 1 Muntanyes Boiroses, 1 Gondor, 4 Mordor. L\'Ull de Sauron a Eriador.'],
  ['Objectius','Destruir l\'Anell Únic i la resta d\'objectius triats, bocamunt. Segueix les seues instruccions de preparació.'],
  ['Personatges','Cada participant pren les seues 2 cartes de personatge i referència, i posa les figures al lloc d\'inici.'],
  ['Cartes de joc','Separa El cel s\'enfosqueix; afegeix els esdeveniments a les 48 de regió, barreja i reparteix la mà inicial. Fes els muntons segons la dificultat, 1 cel enfosquit a cada un, i apila\'ls.'],
  ['Primer torn','Comença qui tinga la carta de regió amb el número més baix (o qui porte Frodo, si és la primera partida).']
];
