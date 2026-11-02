# Paquet d'Android

L'APK de La Comunitat és la mateixa app web (`python3 build.py --web`) dins d'una finestra d'Android,
feta amb [Capacitor](https://capacitorjs.com/) 6. No hi ha codi propi d'Android: el projecte es
genera de nou cada vegada a GitHub Actions (`.github/workflows/publica.yml`, treball `android`).

Les partides es guarden dins de l'app (IndexedDB). Exportar una partida obri el menú «Compartir»
d'Android per a guardar-la a Drive, enviar-la, etc.

## Signatura

Cada versió s'ha de signar sempre amb la mateixa clau; si no, Android no deixa actualitzar l'app
(caldria desinstal·lar-la i es perdrien les partides). La clau es guarda en dos secrets del
repositori (Settings → Secrets and variables → Actions):

- `ANDROID_KEYSTORE`: el fitxer `.p12` en base64.
- `ANDROID_KEYSTORE_PASSWORD`: la contrasenya (la mateixa per al magatzem i per a la clau `comunitat`).

Guardeu una còpia de la clau i de la contrasenya fora de GitHub: si es perden, no es pot recuperar.

## Fer-lo a mà

Cal Node.js 20, JDK 17 i l'SDK d'Android:

```sh
cd paquets/android
npm install
python3 ../../build.py --web www
npx cap add android
python3 ../../eines/android.py --versio 3.0.0 android
npx cap sync android
cd android && ./gradlew assembleDebug
```
