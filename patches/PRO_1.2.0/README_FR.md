# SceneryX — Version PRO_1.2.0

**Date de publication :** 30 Octobre 2026
**Canal :** `Updates/patches`

## NOUVELLES FONCTIONNALITÉS

### 1. Globe Terrestre 3D Interactif & Moteur Cartographique
- **Planisphère 2D & Globe Terrestre 3D (`2D Map` / `3D Globe`) :** Basculez instantanément entre le planisphère 2D Mercator et le nouveau Globe Terrestre 3D avec projection sphérique complète, zoom progressif à la molette, trajectoires orthodromiques 3D et regroupement dynamique des aéroports.
- **8 Styles Cartographiques Unifiés & Cartes Aéronautiques VFR / IFR :** Choisissez parmi 4 thèmes cockpit sombres (`Avionics Blue`, `Deep Navy`, `Carbon Dark`, `Radar Emerald`), les cartes aéronautiques officielles OpenAIP **VFR Chart** et **IFR Enroute** (espaces aériens contrôlés, balises VOR/NDB, fréquences), l'imagerie **Satellite** et **Street Map** en 2D comme en 3D.
- **Terminateur Solaire Jour / Nuit & Timeline UTC / Heure Locale :** Visualisez en temps réel le jour, le crépuscule et la nuit sur la carte 2D et le globe 3D. Parcourez le cycle de 24h via le curseur ou les boutons `-1H` / `+1H`, basculez entre **UTC (Zulu)** et **Heure Locale (`UTC±`)**, ou synchronisez sur l'horloge **LIVE**.

### 2. Optimiseur Unifié Scènes & Route + Éditeur de Règles (`Edit Loadout Rules`)
- **Profils de Scènes de Base Réutilisables (`Edit Loadout Rules`) :** Créez, sauvegardez et activez vos propres profils d'environnement de base (ex. *Europe Airliners*, *North America*) en filtrant par catégorie (`Payware`, `Freeware`, `Asobo`), par région du monde ou par pays.
- **Épinglage d'Aéroports sur la Carte (`Pin Airports on Map`) :** Épinglez vos hubs favoris d'un clic sur la carte 2D ou le globe 3D afin qu'ils restent toujours actifs quelles que soient les règles régionales.
- **Superposition de Route & Dégagements SimBrief :** Combinez votre profil de base avec un trajet **Direct A-to-B**, un **Corridor En-Route** ou une importation **SimBrief OFP** (incluant automatiquement le départ, l'arrivée, le corridor et les aéroports de dégagement SimBrief).

### 3. Télémétrie Live (`DEP / ARR / ACTUAL POSITION`) & Profils Matériels Adaptatifs
- **Nouvel Affichage de Télémétrie de Vol :** Affiche clairement le départ (**DEP**) et l'arrivée (**ARR**) issus de l'OFP SimBrief (ou le point de départ détecté en direct en vol libre) ainsi que la position actuelle de l'avion (**ACTUAL POSITION**).
- **Synchronisation Matérielle Continue :** Adapte dynamiquement les profils de performances (`LOW`, `OPTIMUM`, `ULTRA`) et les cibles Smart LOD selon le CPU, la VRAM GPU, la RAM et la fréquence d'écran détectés, avec mise à jour automatique en cas d'évolution matérielle.
- **Onboarding Interactif Enrichi :** Ajout des badges `NEW` et d'une nouvelle étape dédiée à l'éditeur **Edit Loadout Rules & Profils Personnalisés**.

## BUGS CORRIGÉS & STABILITÉ

### 1. Corrections Globe 3D, Interface & Réglages Graphiques
- **Centrage Optique du Globe 3D à l'Ouverture :** Correction du décalage horizontal du globe 3D au lancement lorsque le panneau latéral Classique est affiché, et ajout d'un `ResizeObserver` automatique.
- **Mise à Jour du Badge `2D` / `VR` & Alignement des Presets Rapides :** Correction de l'indicateur `2D` / `VR` dans le menu latéral et la bannière lors du changement d'onglet (`2D DISPLAY` / `VR HEADSET`), et alignement des 4 clés des boutons rapides 2D et VR (`TerrainLoDFactor`, `ObjectsLoDFactor`, `OffscreenTerrainPreCaching`, `TextureResolution`).
- **Nettoyage du Mode Pin & des Écouteurs de Clic Carte :** Correction de l'interception des clics carte lors de l'ouverture d'un autre tiroir par-dessus le Loadout Builder et restauration propre de l'aperçu carte à la fermeture de la fenêtres.

### 2. Verrous NTFS, Protection Simulateur & Persistance des Données
- **Restauration des BGL Multi-Aéroports :** Correction des fichiers `.bgl.sceneryx_off` orphelins lors du passage direct d'un profil Loadout à un autre et préservation des exclusions manuelles lors d'une restauration partielle.
- **Verrous de Concurrence & Protection MSFS Actif :** Ajout d'un verrou mutex backend (`_scenery_mutation_lock`), vérification stricte de l'état de MSFS (`_is_sim_running_guard`) sur toutes les opérations NTFS et protection anti-double clic côté interface.
- **Sauvegarde Atomique du Cache Matériel :** Remplacement des écritures brutes de `settings.json` par des lectures/écritures sécurisées et suppression de la boucle de redétection RAM au démarrage.
