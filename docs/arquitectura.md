# Arquitectura i comprovacions

`src/servidor.py` coordina HTTP, permisos, revisions i documents de partida. `src/identitats.py` conté normalització, àlies, PIN i registre autoritatiu; s’incrusta en el mateix espai de noms del servidor i no és un paquet independent. `src/persistencia.py` és independent de HTTP i implementa transaccions SQLite, projeccions JSON atòmiques, còpia coherent i bloqueig de la carpeta de dades. `build.py` incrusta els dos mòduls, la finestra, el QR i la web en `comunitat.py`.

El punt de confirmació del guardat és el COMMIT SQLite de l’estat actiu. La base usa `synchronous=FULL` i no manté connexions obertes entre operacions. Les projeccions JSON s’escriuen després amb temporals únics, fsync i substitució atòmica; un error després del COMMIT no desfà una jugada ja durable. Abans de canviar de partida es completa la projecció anterior per no perdre el seu estat. En arrancar es recupera SQLite abans de llegir els JSON. Les partides inactives, les exportacions i les còpies de partida continuen en JSON.

Les comprovacions de fallades no escriuen dades de l’usuari: carpetes temporals, error de disc simulat, projecció parcial, procés que acaba amb transacció SQLite oberta, base corrupta, migració d’historial i recuperació de credencials després d’un error. El bloqueig de dades evita dos servidors de la mateixa app sobre la mateixa carpeta; no bloqueja editors externs ni versions antigues que no implementen el bloqueig.

Comprovacions abans de publicar:

```bash
python3 build.py
python3 eines/comprova-traduccions.py
python3 -m unittest tests.prova_persistencia tests.prova_servidor
python3 tests/prova_navegador.py
python3 eines/web.py /tmp/comunitat-web

git diff --check
```

Les proves de navegador inclouen PC, mòbil, conflictes, reintents i la galeria pública: fletxes, teclat, gest tàctil i càrrega de totes les imatges en VAL/CAS. GitHub repeteix les proves de servidor i persistència en Python 3.8/3.13 i Windows/Linux, i prova les finestres natives dels paquets.
