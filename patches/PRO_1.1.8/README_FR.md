# SceneryX — Patch PRO_1.1.8

**Date de publication :** 22 Octobre 2026
**Canal :** `Updates/patches`

## Nouveautés et Corrections (Inclut v1.1.5, v1.1.6, v1.1.7 & v1.1.8)

### 1. Scanner de Scènes & Mémorisation des Conflits
- **Exclusion stricte et immunité des scènes hors-aéroports :** Exclusion et protection intégrales de tous les packs qui ne sont pas des aéroports (packs de villes et tourisme type SamScene3D `sightseeing`, monuments/Landmarks, POI, photogrammétrie, scènes Asobo/Microsoft hors-aéroports, ponts, navires/marinas, obstacles VFR, lignes électriques, éclairages de nuit et mesh/relief) afin qu'ils ne soient jamais détectés comme des aéroports en conflit ni désactivés.
- **Mémorisation permanente des choix de conflits (`resolved_conflicts`) :** Vos choix dans la fenêtre **Conflit de Scène Détecté** sont désormais enregistrés de façon permanente dans `settings.json` et synchronisés sur tous les fichiers `Content.xml` (y compris pour les aéroports Asobo `StreamedPackages`), afin de ne plus jamais reposer la même question au démarrage.

### 2. Panneau en jeu MSFS 2020/2024 (`sceneryx-ingame-panel`) — VR & Auto-Fit 2D/VR
- **Stabilité VR & Redimensionnement Auto-Fit natif :** Suppression de la boucle de redimensionnement CoherentGT en VR et ajustement vertical automatique en un coup à l'ouverture du tiroir Live Graphics en 2D comme en VR.
- **Traduction complète EN/FR & Info-bulles :** Localisation complète en français et en anglais synchronisée avec SceneryX et info-bulles au survol de toutes les commandes.

### 3. Gestionnaire GSX Pro, Smart LOD & Carte Interactive
- **Fusion intelligente `.ini` + `.py` compagnon :** Association automatique des profils GSX `.ini` et de leur script `.py` compagnon en un seul profil unifié (`+ Python Script`).
- **Offset mémoire MSFS 2024 & Mode Manuel (`MAN`) :** Mise à jour du moteur mémoire temps réel MSFS 2024 et maintien du mode Manuel sur les curseurs `TLOD`/`OLOD`.
- **Fluidité de la carte :** Suppression des carrés clairs lors du zoom et du déplacement sur la carte.
