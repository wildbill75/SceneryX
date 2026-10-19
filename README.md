# ✈️ SceneryX — Next-Generation MSFS Performance & Scenery Suite

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011%20(64--bit)-blue.svg?style=flat-square)
![Simulator](https://img.shields.io/badge/Simulator-MSFS%202020%20%7C%20MSFS%202024-emerald.svg?style=flat-square)
![Architecture](https://img.shields.io/badge/Architecture-x64%20Native%20Desktop-orange.svg?style=flat-square)
![Release](https://img.shields.io/badge/Release-RC__v1.0.8-sky.svg?style=flat-square)
![License](https://img.shields.io/badge/License-Gumroad%20Validated-yellow.svg?style=flat-square)

**SceneryX** est une suite logicielle tout-en-un de nouvelle génération conçue spécifiquement pour les pilotes et passionnés de **Microsoft Flight Simulator (MSFS 2020 & MSFS 2024)**. 

Elle réunit au sein d'une interface cockpit dark ultra-réactive :
1. **La gestion et l'exploration visuelle** de l'ensemble de votre bibliothèque de scènes (Payware, Freeware communautaire, Asobo et scènes streamées MSFS 2024).
2. **Le comparateur de prix en direct** sur plus de 15 boutiques mondiales de simulation de vol.
3. **Le régulateur dynamique de LOD (Smart LOD)** garantissant fluidité absolue et élimination des micro-saccades en vol.
4. **L'optimiseur graphique MSFS & audit matériel** calibrant automatiquement votre UserCfg.opt à la cadence exacte de vos écrans et casques VR.
5. **L'isolateur de scènes par corridor SimBrief** libérant de précieux gigaoctets de mémoire RAM et VRAM.
6. **Le panneau HUD In-Game** déployable directement dans la barre d'outils cockpit de MSFS en 2D et Réalité Virtuelle.
7. **L'enregistreur de vol télémétrique (Blackbox)** fournissant des rapports graphiques complets de fluidité (FPS réels, 1% Low, latence CPU MainThread et consommation VRAM).

---

## 📑 Sommaire / Table of Contents

- [Piliers Fonctionnels](#-piliers-fonctionnels)
  - [1. Exploration Mondiale & Gestionnaire de Scènes](#1-exploration-mondiale--gestionnaire-de-scènes)
  - [2. Comparateur de Prix Payware en Direct](#2-comparateur-de-prix-payware-en-direct)
  - [3. Régulateur Dynamique Smart LOD & Auto Cloud Recovery](#3-régulateur-dynamique-smart-lod--auto-cloud-recovery)
  - [4. Optimisation Graphique & Audit Matériel "My Rig"](#4-optimisation-graphique--audit-matériel-my-rig)
  - [5. Optimiseur de Route de Vol & Isolation SimBrief](#5-optimiseur-de-route-de-vol--isolation-simbrief)
  - [6. Panneau Toolbar In-Game (HUD Cockpit 2D & VR)](#6-panneau-toolbar-in-game-hud-cockpit-2d--vr)
  - [7. Rapports de Performance & Télémétrie en Vol](#7-rapports-de-performance--télémétrie-en-vol)
- [Configuration Requise](#-configuration-requise)
- [Installation & Activation](#-installation--activation)
- [Documentation Utilisateur](#-documentation-utilisateur)
- [Raccourcis Clavier](#-raccourcis-clavier)
- [Support & Mentions Légales](#-support--mentions-légales)

---

## 🚀 Piliers Fonctionnels

### 1. Exploration Mondiale & Gestionnaire de Scènes
* **Mappemonde Interactive Vectorielle** : Cartographie fluide (Leaflet & MarkerCluster) avec clustering dynamique des aérodromes par densité régionale.
* **Deux Ergonomies au Choix** :
  * **Sidebar Classique (Flight Ops)** : Panneau latéral rétractable avec filtres avancés (Modèle économique, Source Community/Official, 11 Régions mondiales, Types de terrain, Profils GSX, Notes communautaires).
  * **Hub Radial Tactique** : Menu circulaire futuriste centré sur chaque aéroport avec 4 quadrants d'accès instantané (Scènes, Lignes aériennes, Pistes, GSX).
* **Détection Multi-Simulateurs** : Analyse conjointe des dossiers `Community`, `Official` et `StreamedPackages` (MSFS 2024).
* **Gestionnaire d'Add-ons & Conflits** : Activation/désactivation chirurgicale de scènes concurrentes sur un même terrain sans quitter l'application.
* **Gestion Complète GSX Pro** : Détection automatique des profils `.ini`, résolution des doublons et glisser-déposer de profils directement sur la carte.

### 2. Comparateur de Prix Payware en Direct
* **Veille Tarifaire Temps Réel** : Requête en direct sur 15+ marketplaces (simMarket, Orbx Direct, Flightbeam, iniBuilds, Aerosoft, France VFR, FlyTampa, FSDreamTeam, Jetstream, LatinVFR, Pyreegue, NZA, Drzewiecki, Contrail, Flightsim.to).
* **Tri Croissant Intelligent** : Présentation du meilleur tarif en tête avec conversion de devises instantanée (USD `$`, EUR `€`, GBP `£`, AUD `A$`).
* **Badge Développeur Officiel** : Mise en valeur dorée `[OFFICIAL DEV]` pour privilégier l'achat direct auprès des créateurs de scènes.
* **Filtre Anti Faux-Positifs** : Exclusion stricte des packs de livrées, textures, éclairages, villes 3D et anciennes versions FSX/P3D.

### 3. Régulateur Dynamique Smart LOD & Auto Cloud Recovery
* **Régulation par Altitude** : Ajustement progressif automatique du Terrain LOD (TLOD) et Objects LOD (OLOD) selon 3 phases de vol (Sol/Approche, Montée/Descente, Croisière).
* **Auto Cloud Recovery** : Réduction temporaire automatique de la densité des nuages volumétriques lors d'un passage en couche dense pour préserver la cadence d'images.
* **Détection de Conflit AutoFPS** : Système de sécurité prévenant la double injection en mémoire en cas de présence simultanée de l'outil externe MSFS AutoFPS.
* **Support Natif OFXR Frame Gen** : Détection du pont OpenXR Toolkit et Frame Generation VR pour un verrouillage parfait de la cadence à 1/2 ou 1/3 Sync.

### 4. Optimisation Graphique & Audit Matériel "My Rig"
* **Audit Matériel en Temps Réel** : Diagnostic CPU (cœurs/threads), GPU (modèle, VRAM, version pilote), RAM (fréquence + statut XMP/EXPO), Stockage NVMe (espace libre MSFS), et visqueux VR.
* **Cadence 1/2 Sync Écran & VR** : Détection automatique de la fréquence de vos moniteurs (60 Hz, 120 Hz, 144 Hz, 165 Hz, 180 Hz, 240 Hz) et calcul automatique du cap de FPS idéal (ex. 180 Hz ➔ 90 FPS, 165 Hz ➔ 82 FPS). Bascule d'écran en **un seul clic**.
* **Éditeur Sécurisé de UserCfg.opt** : Modification directe des paramètres graphiques MSFS (DLSS, Frame Generation, Reflex, Textures, V-Sync) avec système de sauvegarde et de restauration (Rollback) en 1 clic.

### 5. Optimiseur de Route de Vol & Isolation SimBrief
* **Import Direct SimBrief** : Chargement automatique de l'OFP actif via votre identifiant pilote ou nom d'utilisateur.
* **Corridor Dynamique d'Isolation** : Définition d'un couloir de vol personnalisable (de 25 NM à 150 NM) le long de votre trajectoire.
* **Économiseur de RAM & VRAM** : Désactivation temporaire en un clic de tous les aéroports situés hors de votre corridor de vol, prévenant les fuites mémoire et crashs DirectX (DXGI_ERROR_DEVICE_REMOVED).

### 6. Panneau Toolbar In-Game (HUD Cockpit 2D & VR)
* **Intégration Cockpit Dédiée** : Panneau léger déployable directement dans le simulateur via le bouton d'installation des Paramètres.
* **Contrôles en Vol** : Ajustement des curseurs TLOD et OLOD en direct, bascule de l'Auto Cloud Recovery et surveillance des métriques matérielles sans changer de fenêtre.
* **Parfaite Compatibilité VR** : Conçu pour s'intégrer harmonieusement dans les casques de réalité virtuelle sans impacter la fluidité.

### 7. Rapports de Performance & Télémétrie en Vol
* **Enregistreur Télémétrique Haute Fréquence** : Capture continue des métriques clés (FPS réels, FPS de base sans Frame Gen, 1% Low, latence MainThread CPU en millisecondes, charge GPU, utilisation VRAM et RAM).
* **Rapports Détaillés & Graphiques** : Analyse post-vol interactive avec repérage précis des micro-saccades, des goulots d'étranglement (CPU vs GPU bound) et conseils personnalisés d'optimisation.

---

## 💻 Configuration Requise

| Composant | Configuration Minimale | Configuration Recommandée |
| :--- | :--- | :--- |
| **Système d'exploitation** | Windows 10 (64-bit, 20H2+) | Windows 11 (64-bit, 23H2+) |
| **Simulateur** | MSFS 2020 ou MSFS 2024 | MSFS 2020 / MSFS 2024 (Dossiers Community accessibles) |
| **Processeur** | 6 cœurs physiques (ex. i5-10400 / Ryzen 3600) | 8+ cœurs (ex. i7-13700K / Ryzen 7800X3D) |
| **Mémoire Vive (RAM)** | 16 Go DDR4 (3200 MHz) | 32 Go ou 64 Go DDR5 avec XMP/EXPO activé |
| **Carte Graphique** | 8 Go VRAM (NVIDIA RTX 2060 / AMD RX 6600) | 12+ Go VRAM (RTX 4070 / RTX 4080 / RTX 4090 / RX 7900) |
| **Stockage** | SSD NVMe avec au moins 2 Go libres pour l'app | SSD NVMe PCIe 4.0 avec 50+ Go libres pour MSFS Packages |
| **Affichage** | Résolution minimale 1920x1080 | 2560x1440 ou 4K avec G-Sync / FreeSync |

---

## 📦 Installation & Activation

1. Téléchargez la dernière version d'installation : **`SceneryX_RC_v1.0.8_Setup.exe`**.
2. Exécutez l'installeur avec les privilèges Administrateur.
3. Lisez et acceptez le contrat de licence (EULA).
4. À l'écran d'activation, renseignez votre clé de licence Gumroad (ou clé permanente de test `SCNX-MASTER-2026-OK`).
5. L'installeur configure automatiquement les dossiers dans `%APPDATA%\SceneryX` et génère vos profils standard optimisés (2D Display Standard et VR Headset Standard) d'après votre matériel.
6. Lancez SceneryX : l'audit initial détecte immédiatement vos dossiers MSFS et vos équipements.

---

## 📖 Documentation Utilisateur

Pour une prise en main visuelle pas à pas, deux documents complets sont mis à votre disposition :

* **[USER_MANUAL.md](docs/USER_MANUAL.md)** : Le manuel complet en Markdown avec tous les encarts de capture d'écran détaillés.
* **[SceneryX_User_Manual.docx](docs/SceneryX_User_Manual.docx)** : Le document Word officiel préformaté avec emplacements dédiés pour intégrer vos captures d'écran et imprimer ou exporter en PDF.

---

## ⌨️ Raccourcis Clavier

| Raccourci | Action |
| :--- | :--- |
| **Échap (`Esc`)** | Ferme la modale, le drawer ou la bulle d'aide contextuelle active |
| **Entrée (`Enter`)** | Valide la recherche dans la barre d'aéroports mondiale |
| **Clic Molette / Glisser** | Déplacement panoramique fluide sur la carte du monde |
| **Molette Haut / Bas** | Zoom avant / Zoom arrière sur les aéroports et clusters |
| **Double Clic Aéroport** | Centre la caméra et ouvre la vue détaillée du terrain |

---

## 🛡️ Support & Mentions Légales

* **Éditeur** : Sidestick Priority
* **Dépôt Officiel** : [https://github.com/wildbill75/SceneryX](https://github.com/wildbill75/SceneryX)
* **Détection & Respect des Fichiers Originaux** : SceneryX effectue systématiquement une copie de sauvegarde non altérée de votre `UserCfg.opt` avant toute première modification (`UserCfg_Original_Pristine.opt.bak`). Vous pouvez restaurer vos réglages d'origine à tout moment en un clic.
* **Marques déposées** : Microsoft Flight Simulator est une marque déposée de Microsoft Corporation. GSX Pro est un produit de FSDreamTeam. SceneryX est un utilitaire indépendant développé pour la communauté des simulateurs de vol.
