# SceneryX — Patch PRO_1.1.7

**Date de publication :** 21 Octobre 2026
**Canal :** `Updates/patches`

## Nouveautés et Corrections (Inclut v1.1.5, v1.1.6 & v1.1.7)

### 1. Gestionnaire GSX Pro & Fluidité de la Carte
- **Fusion intelligente des profils `.ini` + `.py` compagnon :** Correction d'un problème où les archives GSX contenant à la fois un fichier `.ini` et un script Python `.py` avec un identifiant Flightsim.to différent dans le nom (ex. `lpma-7ryin1-amsim-zwackelpeter.ini` + `lpma-amsim-zwackelpeter.py`) étaient détectées à tort comme deux profils en conflit (`DUPLICATE`) au lieu d'être regroupées en un seul profil complet avec le badge `+ Python Script`.
- **Synchronisation Activation / Désactivation / Suppression :** L'activation, la désactivation, la suppression ou la résolution de doublons sur un profil GSX conserve et gère désormais systématiquement le couple `.ini` + `.py` ensemble.
- **Fluidité du zoom et du rendu de la carte :** Suppression des carrés clairs de superposition lors du zoom/déplacement de la carte et optimisation du cache de dalles pour des transitions fluides et sans artefacts.

### 2. Panneau en jeu MSFS 2020/2024 (`sceneryx-ingame-panel`) — Correctif VR & VRAM
- **Correction de la saturation VRAM en VR :** Suppression de la boucle de redimensionnement CoherentGT (`content-fit` / `sendUpdatePanelSize`) qui réallouait en continu les textures 3D du panneau en VRAM lors de l'ouverture du panneau en VR sur les appareils lourds (ex. Fenix A320).
- **Traduction complète EN/FR & Info-bulles contextuelles :** Ajout de la localisation complète en français et en anglais synchronisée avec SceneryX, ainsi que d'info-bulles contextuelles sur l'ensemble des réglages Live Graphics, curseurs Smart LOD, Auto Cloud Recovery et jauges de performance.
- **Nommage unifié & Mise à jour auto :** Le package Community se nomme désormais `sceneryx-ingame-panel` (avec migration automatique de l'ancien dossier au démarrage) tout en conservant le titre `SCENERY X` dans l'en-tête.

### 3. Régulation Smart LOD & Moteur Mémoire Temps Réel
- **Offset mémoire MSFS 2024 & Scanner de signature :** Mise à jour de l'offset mémoire (`0x0A80B024`) pour la dernière version de `FlightSimulator2024.exe` avec scanner automatique de signature `.data` assurant l'écriture en direct (`TLOD`, `OLOD`, `Nuages` et réglages graphiques).
- **Maintien du mode Manuel (`MAN`) :** Correction d'un bug dans le panneau en jeu et la fenêtre Smart LOD où la désactivation du Smart LOD (`OFF`) ou le déplacement manuel des curseurs `TLOD` / `OLOD` réactivait le mode `ON` au bout de 2 secondes.

### 4. Profils Graphiques, Sauvegarde des Paramètres & Détection des Doublons
- **Protection atomique de `settings.json` :** Sécurisation des préférences utilisateur (langue, thème, fermeture dans la barre des tâches, dossiers de scan, identifiant SimBrief) contre toute réinitialisation lors des mises à jour ou scans simultanés.
- **Sauvegarde et bascule de profils indépendantes :** Modifier un réglage dans la matrice graphique n'écrase plus le fichier `.profile.json` actif avant d'avoir cliqué sur `SAUVEGARDER LE PROFIL`, et le changement de profil met immédiatement à jour la matrice et `UserCfg.opt`.
- **Détection des doublons Scènes & GSX :** Restauration complète de la détection des doublons d'aéroports multi-dossiers (`Community`, `Official`, `StreamedPackages`, Addon Linker).
