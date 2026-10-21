# SceneryX — Patch PRO_1.1.6

**Date de publication :** 21 Octobre 2026
**Canal :** `Updates/patches`

## Nouveautés et Corrections (Inclut v1.1.5 & v1.1.6)

### 1. Panneau en jeu MSFS 2020/2024 (`sceneryx-ingame-panel`)
- **Ajustement automatique de la hauteur :** Le panneau en jeu MSFS adapte désormais automatiquement sa hauteur verticale à son contenu en temps réel (ouverture/fermeture du tiroir Live Graphics, passage Hors-ligne / En ligne) tout en restant redimensionnable en largeur.
- **Traduction complète EN/FR & Info-bulles contextuelles :** Ajout de la localisation complète en français et en anglais synchronisée avec SceneryX, ainsi que d'info-bulles contextuelles sur l'ensemble des réglages Live Graphics, curseurs Smart LOD, Auto Cloud Recovery et jauges de performance.
- **Nommage unifié & Mise à jour auto :** Le package Community se nomme désormais `sceneryx-ingame-panel` (avec migration automatique de l'ancien dossier au démarrage) tout en conservant le titre `SCENERY X` dans l'en-tête.

### 2. Régulation Smart LOD & Moteur Mémoire Temps Réel
- **Offset mémoire MSFS 2024 & Scanner de signature :** Mise à jour de l'offset mémoire (`0x0A80B024`) pour la dernière version de `FlightSimulator2024.exe` avec scanner automatique de signature `.data` assurant l'écriture en direct (`TLOD`, `OLOD`, `Nuages` et réglages graphiques).
- **Maintien du mode Manuel (`MAN`) :** Correction d'un bug dans le panneau en jeu et la fenêtre Smart LOD où la désactivation du Smart LOD (`OFF`) ou le déplacement manuel des curseurs `TLOD` / `OLOD` réactivait le mode `ON` au bout de 2 secondes.

### 3. Profils Graphiques & Détection des doublons Scènes / GSX
- **Sauvegarde et bascule de profils indépendantes :** Modifier un réglage dans la matrice graphique n'écrase plus le fichier `.profile.json` actif avant d'avoir cliqué sur `SAUVEGARDER LE PROFIL`, et le changement de profil met immédiatement à jour la matrice et `UserCfg.opt`.
- **Détection des doublons Scènes & GSX :** Restauration complète de la détection des doublons d'aéroports multi-dossiers (`Community`, `Official`, `StreamedPackages`, Addon Linker) et des conflits de profils GSX lors du Re-scan Packages.
