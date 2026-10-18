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
/* ---------- Dades del joc (del manual en castellà, traduïdes) ---------- */
const CHARACTERS=[
  {id:'frodosam',name:'Frodo i Sam',start:'La Comarca',color:'#C99A2E',frodo:true},
  {id:'merrypippin',name:'Merry i Pippin',start:'La Comarca',color:'#D07A2C'},
  {id:'aragorn',name:'Aragorn',start:'Turons del Vent',color:'#6A4C9C'},
  {id:'arwen',name:'Arwen',start:'Rivendell',color:'#7FA83A'},
  {id:'boromir',name:'Boromir',start:'Minas Tirith',color:'#2D4F95'},
  {id:'eomer',name:'Éomer',start:'Eastemnet',color:'#8A5A2B'},
  {id:'eowyn',name:'Éowyn',start:'Edoras',color:'#B9A27A'},
  {id:'faramir',name:'Faramir',start:'Minas Tirith',color:'#3E83C4'},
  {id:'galadriel',name:'Galadriel',start:'Lòrien',color:'#3C6E3F'},
  {id:'gandalf',name:'Gandalf',start:'Tharbad',color:'#9AA0A6'},
  {id:'gimli',name:'Gimli',start:'Erebor',color:'#5E6670'},
  {id:'gollum',name:'Gollum',start:'Mòria',color:'#2E2E2E'},
  {id:'legolas',name:'Legolas',start:'Regne del Bosc',color:'#86B33F'}
];
const SUGGESTED=[['frodosam','legolas'],['merrypippin','eowyn'],['arwen','aragorn'],['gandalf','boromir'],['gimli','eomer']];
const OBJECTIVES=['Rebre la benedicció dels elfs','«Saruman, el teu bastó està trencat»','Desafiar Sauron','Enfrontar-se al Balrog','Els perjurs compleixen el seu deure','Sotmetre Umbar','Cavalcar amb els Éored','Alliberar la ment de Théoden','Fer front als hereus de Freca','Mai més una donzella guerrera','«Ja en porte sis!»','Arwen desplega l\'estendard','Deixar al descobert les masmorres','Portar la llum al Bosc Fosc','La redempció de Boromir','Assegurar el gual de l\'Anduin','Destronar Denethor','Infiltrar-se a Minas Morgul','Venjar Balin!','Desterrar l\'Ombra de les terres nanes','Els forestals asseguren Eriador','Els hòbbits juren lleialtat','El cau de l\'Aranya'];
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
  ['Marcadors','Amenaça i esperança a la casella amb punt del seu medidor (l\'esperança, a la 6).'],
  ['Mazo d\'Ombra','Les 2 cartes especials (Sauron i Saruman) a la pila de descarts d\'Ombra; barreja la resta i fes el mazo.'],
  ['Tropes aliades','Nans: Ered Luin, Erebor, Turons de Ferro. Elfs: Ports Grisos, Rivendell, Lòrien, Regne del Bosc. Rohirrim: Abisme de Helm, Edoras, Eastemnet. Gondor: 2 a Minas Tirith, 2 a Dol Amroth, 1 a Pelargir.'],
  ['Tropes de l\'Ombra','1 Terres Brunes, 1 Isengard, 2 Mòria, 1 Dol Guldur, 3 Rhûn, 2 Minas Morgul, 2 Barad-dûr, 3 Núrn, 1 Umbar, 2 Harad Pròxim. Després roba 9 cartes d\'Ombra i posa 1 tropa al lloc roig de cada una; descarta-les.'],
  ['Natzguls i Ull','Natzguls: 2 Eriador, 1 Rhudaur, 1 Muntanyes Boiroses, 1 Gondor, 4 Mordor. L\'Ull de Sauron a Eriador.'],
  ['Objectius','Destruir l\'Anell Únic i la resta d\'objectius triats, bocamunt. Segueix les seues instruccions de preparació.'],
  ['Personatges','Cada participant pren les seues 2 cartes de personatge i referència, i posa les figures al lloc d\'inici.'],
  ['Cartes de joc','Separa El cel s\'enfosqueix; afegeix els esdeveniments a les 48 de regió, barreja i reparteix la mà inicial. Fes els muntons segons la dificultat, 1 cel enfosquit a cada un, i apila\'ls.'],
  ['Primer torn','Comença qui tinga la carta de regió amb el número més baix (o qui porte Frodo, si és la primera partida).']
];
