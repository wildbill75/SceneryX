# 📘 SceneryX — Manuel d'Utilisation & Guide Officiel
**Version du document :** 1.0.5  
**Version de l'application :** SceneryX RC_v1.0.5  
**Éditeur :** Sidestick Priority  
**Plateforme :** Windows 10 & 11 (64-bit) — Microsoft Flight Simulator 2020 & 2024  

---

## 📑 Table des Matières

1. [Introduction & Architecture Générale](#1-introduction--architecture-générale)
2. [Installation, Clé de Licence & Premier Lancement](#2-installation-clé-de-licence--premier-lancement)
3. [Interface Principale & Ergonomies de Navigation](#3-interface-principale--ergonomies-de-navigation)
   - 3.1 Mode Sidebar Classique (Flight Ops)
   - 3.2 Mode Hub Radial Tactique
4. [Gestionnaire de Bibliothèque de Scènes & Filtres Avancés](#4-gestionnaire-de-bibliothèque-de-scènes--filtres-avancés)
5. [Hub Aéroport, Gestion Multi-Scènes & Profils GSX Pro](#5-hub-aéroport-gestion-multi-scènes--profils-gsx-pro)
6. [Comparateur de Prix Payware en Direct (Store Comparator)](#6-comparateur-de-prix-payware-en-direct-store-comparator)
7. [Optimiseur de Route de Vol & Isolation SimBrief](#7-optimiseur-de-route-de-vol--isolation-simbrief)
8. [Régulateur Dynamique Smart LOD & Auto Cloud Recovery](#8-régulateur-dynamique-smart-lod--auto-cloud-recovery)
9. [Diagnostic Matériel « MY RIG » & Cadence d'Écran](#9-diagnostic-matériel--my-rig--cadence-décran)
10. [Optimiseur Graphique MSFS & Gestion du UserCfg.opt](#10-optimiseur-graphique-msfs--gestion-du-usercfgopt)
11. [Panneau In-Game Cockpit (Toolbar HUD 2D & VR)](#11-panneau-in-game-cockpit-toolbar-hud-2d--vr)
12. [Enregistreur Télémétrique & Rapports de Performance](#12-enregistreur-télémétrique--rapports-de-performance)
13. [Paramètres, Caméras & Préférences Générales](#13-paramètres-caméras--préférences-générales)

---

## 1. Introduction & Architecture Générale

**SceneryX** est une suite intégrée de gestion et d'optimisation de performances pour Microsoft Flight Simulator. Conçue autour d'un moteur asynchrone ultra-léger et d'une interface inspirée des cockpits modernes (FMS / EFIS dark mode), elle offre aux pilotes virtuels une maîtrise totale sur leur écosystème de vol :

* **Zéro altération destructive** : Vos fichiers originaux MSFS (dont le précieux `UserCfg.opt`) sont systématiquement sauvegardés dans leur état d'origine intact avant toute modification.
* **Intégration transparente MSFS 2020 & MSFS 2024** : Détection conjointe des dossiers `Community`, des bibliothèques officielles sur disque et des scènes streamées du cloud.
* **Synchronisation parfaite de cadence** : Élimination du micro-stuttering par synchronisation 1/2 Sync calculée directement sur le taux de rafraîchissement physique de votre écran et de votre casque VR.

---

## 2. Installation, Clé de Licence & Premier Lancement

L'installation de SceneryX est gérée par un installeur Windows sécurisé 64 bits (`SceneryX_RC_v1.0.5_Setup.exe`).

### Procédure d'installation :
1. Lancez l'installeur en tant qu'administrateur.
2. Si une version précédente est détectée, l'assistant vous propose une mise à jour transparente en préservant l'intégralité de vos réglages et préférences.
3. À l'écran d'activation, renseignez votre clé de licence Gumroad (ou clé permanente de test `SCNX-MASTER-2026-OK`).
4. L'installeur analyse immédiatement les composants de votre machine pour initialiser deux profils de base optimisés dans `%APPDATA%\SceneryX\custom_profiles\` :
   * `profile_2d_display_standard.profile.json` (calibré pour votre moniteur principal).
   * `profile_vr_headset_standard.profile.json` (calibré pour la réalité virtuelle).

> 📸 **ENCART CAPTURE D'ÉCRAN N°1 : Assistant d'Installation & Validation de Licence**
> ```text
> [ EMPLACEMENT CAPTURE D'ÉCRAN N°1 ]
> • Écran à capturer : Fenêtre de l'installeur Inno Setup (SceneryX Setup).
> • Étape affichée : Page "Product License Activation / Activation de la Licence".
> • Éléments visibles : Le champ de saisie de la clé de licence Gumroad avec la clé renseignée, les boutons [Next >] et [Cancel].
> • Cadrage recommandé : Capture centrée sur la fenêtre de l'assistant (environ 700x500 px).
> • Légende : Figure 1 — Écran d'activation de la licence lors de l'installation de SceneryX.
> ```

---

## 3. Interface Principale & Ergonomies de Navigation

SceneryX propose deux approches ergonomiques distinctes, permutables à tout moment depuis les Paramètres ou la barre d'outils.

### 3.1 Mode Sidebar Classique (Flight Ops)
La **Sidebar Classique** rétractable (à gauche de l'écran) regroupe l'ensemble des modules d'analyse, des filtres d'aéroports et des statistiques de collection dans une disposition familière aux habitués des suites EFB / Flight Planning.

### 3.2 Mode Hub Radial Tactique
Le **Hub Radial** est un menu contextuel circulaire ultra-immersif centré directement sur l'aérodrome sélectionné. Il permet d'interroger en un clin d'œil les 4 aspects clés d'un terrain via ses quadrants :
* **Quadrant Nord (Haut)** : Liste des scènes installées et gestion des doublons.
* **Quadrant Est (Droite)** : Compagnies aériennes régulières et carte de leurs destinations.
* **Quadrant Sud (Bas)** : Pistes, dimensions, orientation magnétique, fréquences et balisage.
* **Quadrant Ouest (Gauche)** : Statut et gestion du profil GSX Pro.

> 📸 **ENCART CAPTURE D'ÉCRAN N°2 : Écran Principal — Vue Mappemonde Globale**
> ```text
> [ EMPLACEMENT CAPTURE D'ÉCRAN N°2 ]
> • Écran à capturer : Fenêtre principale complète de SceneryX après démarrage.
> • Éléments visibles : Mappemonde Leaflet avec les clusters d'aéroports colorés par région, barre de statistiques supérieure (Payware, Freeware, Asobo, Investissement global), barre de recherche et d'actions en bas.
> • Cadrage recommandé : Plein écran 16:9 (1920x1080 ou 2560x1440).
> • Légende : Figure 2 — Interface principale de SceneryX avec la cartographie mondiale interactive des scènes.
> ```

> 📸 **ENCART CAPTURE D'ÉCRAN N°3 : Le Hub Radial Tactique en Action (ex. LPMA)**
> ```text
> [ EMPLACEMENT CAPTURE D'ÉCRAN N°3 ]
> • Écran à capturer : Clic sur un aéroport majeur (ex. LPMA Madeira ou KJFK New York).
> • Éléments visibles : Le cercle central affichant l'ICAO et les 4 quadrants interactifs déployés au-dessus de l'aérodrome avec le fond de carte centré.
> • Cadrage recommandé : Zoom rapproché sur le menu radial (environ 900x700 px).
> • Légende : Figure 3 — Le Hub Radial interactif déployé sur l'aéroport de Funchal (LPMA).
> ```

---

## 4. Gestionnaire de Bibliothèque de Scènes & Filtres Avancés

Le panneau latéral gauche intègre un moteur de filtrage multicritère instantané :

1. **Modèle Économique (Pricing Model)** :
   * `PAYWARE` : Scènes commerciales achetées auprès d'éditeurs tiers.
   * `FREEWARE` : Créations communautaires gratuites (Flightsim.to, etc.).
   * `ASOBO / MSFS` : Terrains façonnés à la main (*Handcrafted*) issus des World Updates officiels.
   * `DEFAULT` : Aérodromes procéduraux natifs de MSFS.
2. **Source du Package (Scenery Source)** :
   * `COMMUNITY` : Packages locaux installés manuellement dans votre dossier Community.
   * `OFFICIAL` : Contenu officiel acheté sur le Marketplace MSFS (OneStore / Steam).
   * `STREAMED` : Contenu cloud dynamique de MSFS 2024.
3. **Région du Monde (World Region)** : Isolation géographique en 1 clic parmi 11 zones mondiales (Europe de l'Ouest, Amérique du Nord, Asie, Océanie...).
4. **Catégorie d'Aérodrome (Airport Category)** : Grands hubs Internationaux, terrains Régionaux, Aviation Générale (GA / pistes en herbe), Hydrobases ou Héliports.
5. **Profil GSX (GSX Profile)** : Filtrage instantané des terrains disposant d'un profil de pushback et de véhicules configuré.

> 📸 **ENCART CAPTURE D'ÉCRAN N°4 : Panneau des Filtres Multicritères (Mode Classique)**
> ```text
> [ EMPLACEMENT CAPTURE D'ÉCRAN N°4 ]
> • Écran à capturer : Sidebar gauche de SceneryX avec les accordéons de filtres ouverts.
> • Éléments visibles : Accordéons "Pricing Model", "Scenery Source", "World Region" avec des coches actives et le compteur d'aéroports filtrés mis à jour.
> • Cadrage recommandé : Colonne latérale gauche et bordure de carte (environ 450x900 px).
> • Légende : Figure 4 — Panneau de filtres multicritères permettant d'isoler n'importe quelle catégorie de scènes.
> ```

---

## 5. Hub Aéroport, Gestion Multi-Scènes & Profils GSX Pro

Lorsque plusieurs scènes concurrentes sont installées pour un même aérodrome (par exemple une version payware Flightbeam et une version World Update Asobo), SceneryX met immédiatement en évidence le conflit.

### Gestionnaire d'Add-ons Dédié :
* **Interrupteur ON/OFF individuel** : Désactivez une scène sans devoir la supprimer de votre disque dur (SceneryX renomme le dossier de manière standardisée et sécurisée).
* **Isolation 1-Clic** : Le bouton « Isoler » active la scène choisie et désactive automatiquement toutes ses concurrentes pour garantir l'absence de textures superposées ou de bugs d'élévation.

### 5.1 Scènes Complètes vs Fixes & Overlays Cumulables (Available Fixes)
* **Scènes Complètes (Mutuellement Exclusives)** : Les scènes complètes d'un même aéroport (Payware, Freeware complet, Asobo / World Update, Aérodrome par défaut) s'excluent mutuellement. Pour éviter les artefacts visuels, doublons de pistes ou conflits géométriques, une seule scène de base doit être active à la fois.
* **Available Fixes & Overlays (Cumulables & Stackables)** : À l'inverse, les correctifs légers et surcouches additionnelles (patchs de taxiways, éclairage nocturne amélioré, retouches photogrammétriques, profils GSX Pro) sont **totalement cumulables**. Ils possèdent des commutateurs indépendants et viennent se superposer harmonieusement au-dessus de la scène principale sélectionnée, sans déclencher de conflit.

### 5.1 Scènes Complètes vs Fixes & Overlays Cumulables (Available Fixes)
* **Scènes Complètes (Mutuellement Exclusives)** : Les scènes complètes d'un même aéroport (Payware, Freeware complet, Asobo / World Update, Aérodrome par défaut) s'excluent mutuellement. Pour éviter les artefacts visuels, doublons de pistes ou conflits géométriques, une seule scène de base doit être active à la fois.
* **Available Fixes & Overlays (Cumulables & Stackables)** : À l'inverse, les correctifs légers et surcouches additionnelles (patchs de taxiways, éclairage nocturne amélioré, retouches photogrammétriques, profils GSX Pro) sont **totalement cumulables**. Ils possèdent des commutateurs indépendants et viennent se superposer harmonieusement au-dessus de la scène principale sélectionnée, sans déclencher de conflit.

### Intégration GSX Pro :
* Détection automatique des profils `.ini` présents dans `%APPDATA%\Virtuali\GSX\MSFS`.
* Glisser-déposer (*Drag & Drop*) : faites glisser n'importe quel fichier `.ini` téléchargé directement sur la carte pour l'associer et l'installer instantanément sur le bon aérodrome.

> 📸 **ENCART CAPTURE D'ÉCRAN N°5 : Modale des Scènes Disponibles & Résolution de Conflits**
> ```text
> [ EMPLACEMENT CAPTURE D'ÉCRAN N°5 ]
> • Écran à capturer : Fenêtre modale "Available Add-ons" sur un aéroport possédant plusieurs scènes (ex. LFPG ou EGLL).
> • Éléments visibles : Liste des versions (Payware vs Asobo), interrupteurs à bascule vert/gris, badge d'état et chemin physique sur le disque.
> • Cadrage recommandé : Modale centrée (environ 650x500 px).
> • Légende : Figure 5 — Gestionnaire multi-scènes et résolution de doublons pour un même terrain.
> ```

---

## 6. Comparateur de Prix Payware en Direct (Store Comparator)

Le comparateur de prix interroge en temps réel les catalogues de plus de 15 distributeurs et boutiques de développeurs officiels.

* **Tri par prix croissant** : La meilleure offre actuelle apparaît toujours en tête.
* **Badge doré `[OFFICIAL DEV]`** : Identifie immédiatement la boutique du créateur original pour soutenir directement les développeurs tiers.
* **Multi-devises** : Affichage transparent en EUR (€), USD ($), GBP (£) ou AUD (A$) selon vos préférences.

> 📸 **ENCART CAPTURE D'ÉCRAN N°6 : Comparateur de Prix Payware en Temps Réel**
> ```text
> [ EMPLACEMENT CAPTURE D'ÉCRAN N°6 ]
> • Écran à capturer : Fenêtre "Payware Scenery Search" ouverte sur une scène majeure (ex. LFMN Nice Côte d'Azur ou LOWI Innsbruck).
> • Éléments visibles : Tableau comparatif des boutiques (Orbx, simMarket, iniBuilds...), prix convertis, badge vert du tarif le plus bas et badge doré [OFFICIAL DEV].
> • Cadrage recommandé : Fenêtre du comparateur bien cadrée (environ 750x550 px).
> • Légende : Figure 6 — Comparateur de prix en direct affichant les offres multi-boutiques pour une même scène.
> ```

---

## 7. Optimiseur de Route de Vol & Isolation SimBrief

Le module **Flight Route Optimization** résout l'une des causes majeures de ralentissements et de crashs mémoire dans MSFS : le chargement en arrière-plan de centaines d'aéroports détaillés inutiles situés à des milliers de kilomètres de votre vol.

### Comment utiliser l'optimiseur de corridor :
1. Ouvrez la fenêtre flottante **Flight Route Optimization**.
2. Renseignez votre identifiant SimBrief et cliquez sur **« Importer l'OFP Actif »** (ou entrez manuellement votre aéroport de départ et d'arrivée).
3. Définissez la largeur du couloir de vol souhaitée (ex. 60 NM autour de la trajectoire).
4. SceneryX trace le corridor sur la carte mondiale et calcule instantanément le volume de RAM et VRAM qui sera économisé.
5. Cliquez sur **« Isoler le Corridor »** : toutes les scènes hors trajectoire sont temporairement mises en sommeil. Vous pouvez les restaurer d'un simple clic à l'atterrissage.

> 📸 **ENCART CAPTURE D'ÉCRAN N°7 : Fenêtre d'Optimisation de Route & Corridor SimBrief**
> ```text
> [ EMPLACEMENT CAPTURE D'ÉCRAN N°7 ]
> • Écran à capturer : Fenêtre flottante "Flight Route Optimization" superposée à la carte mondiale.
> • Éléments visibles : Route tracée entre deux aérodromes (ex. LFPG Paris ➔ LPMA Funchal), polygone de corridor bleuté, estimation des Go libérés et bouton d'action "Isolate Route Corridor".
> • Cadrage recommandé : Vue d'ensemble montrant la fenêtre flottante et la trace du vol sur la carte (environ 1100x700 px).
> • Légende : Figure 7 — Tracé du corridor de vol SimBrief et isolation des scènes pour préserver la mémoire système.
> ```

---

## 8. Régulateur Dynamique Smart LOD & Auto Cloud Recovery

Le **Smart LOD** de SceneryX est un gouverneur d'affichage intelligent qui fait varier la complexité géométrique de l'environnement selon votre altitude de vol réelle :

* **Au sol / En approche** : Le Terrain LOD (TLOD) est volontairement contenu pour délester le MainThread CPU sur les gros aéroports saturés de trafic et de passerelles.
* **En montée / Transition** : Le TLOD augmente progressivement à mesure que la ligne d'horizon s'élargit.
* **En croisière (haute altitude)** : Le TLOD atteint son palier maximal pour offrir une visibilité panoramique époustouflante sur les reliefs montagneux et côtes, alors que les bâtiments au sol ne pèsent plus sur le CPU.
* **Auto Cloud Recovery** : Si une couverture nuageuse dense (Overcast / Cumulonimbus) fait chuter le framerate sous votre seuil de confort, SceneryX adapte temporairement la finesse des nuages pour maintenir une cadence sans à-coups.

> 📸 **ENCART CAPTURE D'ÉCRAN N°8 : Panneau de Contrôle Smart LOD & Paliers d'Altitude**
> ```text
> [ EMPLACEMENT CAPTURE D'ÉCRAN N°8 ]
> • Écran à capturer : Fenêtre flottante "Smart LOD & Auto FPS".
> • Éléments visibles : Les curseurs Ground, Transition et Cruise pour le TLOD et l'OLOD, l'interrupteur Auto Cloud Recovery (vert/actif), et le badge de statut de synchronisation des FPS.
> • Cadrage recommandé : Fenêtre flottante Smart LOD (environ 600x500 px).
> • Légende : Figure 8 — Régulateur dynamique Smart LOD adaptant la finesse géométrique selon l'altitude de vol.
> ```

---

## 9. Diagnostic Matériel « MY RIG » & Optimiseur Système

La fenêtre flottante **MY RIG & SYSTEM** propose un centre de contrôle à double volet rigoureusement différencié : l'optimiseur d'environnement Windows / GPU hors-simulateur (**System Optimizer**) et l'architecture matérielle détaillée couplée à la calibration d'affichage (**Hardware Specs**).

SceneryX intègre un moteur de détection matérielle automatisé qui sonde instantanément les composants physiques de votre rig (cœurs/threads du processeur, architecture et VRAM de la carte graphique, fréquence RAM et profil XMP/EXPO, débits de stockage SSD NVMe, cadence des moniteurs et casques VR connectés). **Toutes les recommandations d'optimisation, paliers Smart LOD et profils de simulateur sont ainsi calculés sur-mesure d'après la baseline matérielle réelle de votre PC.**

Un bouton d'aide contextuel **« ? »** présent dans la barre de titre affiche à tout moment les explications et consignes précises selon l'onglet actuellement sélectionné.

### 9.1 System Optimizer (Optimisation Hors-Simulateur Windows & GPU)
L'onglet **System Optimizer** arbore un bandeau d'état **WINDOWS DIAGNOSIS** avec une pilule verte **OPTIMAL** justifiée à droite (un peu plus large que les badges individuels). Il audite et calibre 7 paramètres système et DirectX essentiels :
* **Planification GPU à accélération matérielle (HAGS)** : Délègue l'ordonnancement de la VRAM directement au GPU, abaissant la latence et strictement obligatoire pour **DLSS 3 Frame Generation**. La modale simplifiée **GPU SCHEDULING (HAGS)** (en anglais, sans encadré jaune ni icône d'avertissement) condense les consignes, offre l'accès direct aux Paramètres Windows 11/10 et intègre un commutateur UAC écrivant directement la clé `HwSchMode` dans le registre (*rappel : un redémarrage PC est requis par Windows pour appliquer tout changement de HAGS*).
* **DirectX Shader Cache (Occupation disque & Quota GPU)** : SceneryX mesure en temps réel l'occupation cumulée sur disque des nuanceurs DirectX et GPU (`D3DSCache`, `DXCache`, `GLCache`, etc.). La modale **DIRECTX SHADER CACHE** (en anglais) distingue clairement l'occupation actuelle sur disque du quota alloué dans le pilote (recommandé à **10 Go** ou **Illimité** dans l'application GPU). Elle propose un bouton d'accès direct vers **NVIDIA App** (avec barre latérale de navigation complète et repli transparent vers le Panneau NVIDIA classique si la nouvelle application n'est pas installée), l'utilitaire Windows `cleanmgr.exe` et un outil de purge directe en teinte neutre (sans jaune) libérant les fichiers corrompus ou saturés.
* **Mode Jeu Windows (Windows Game Mode)** : Réserve la priorité des threads CPU au processus `FlightSimulator.exe`, neutralisant les tâches d'arrière-plan intempestives via un commutateur à bascule direct.
* **Plan d'Alimentation Windows (Power Plan)** : Commutation en un clic vers le profil « Performances Élevées » ou « Performances Ultimes », éliminant le bridage énergétique du CPU.
* **Re-Size BAR (Base Address Register)** : Détection de l'accès direct du CPU à l'intégralité de la VRAM vidéo. Guide interactif d'activation UEFI BIOS pas-à-pas en cas d'inactivité.
* **Pilote Graphique GPU & Panneau de Contrôle** : Analyse de la carte graphique, comparaison de version avec les derniers pilotes certifiés WHQL en ligne, et accès rapide aux outils de contrôle dans la modale **GPU DRIVER & CONTROL PANEL**.
* **Virtualization-Based Security (VBS / HVCI)** : Détection de l'isolation du noyau Windows pour évaluer son impact sur les simulateurs de vol lourds.

### 9.2 Hardware Specs & Sélection d'Écran Haute Fréquence
L'onglet **Hardware Specs** présente un bandeau supérieur **RIG ARCHITECTURE** avec pilule verte **OPTIMAL** justifiée à droite. L'évaluation de l'équilibre des composants (CPU, GPU et RAM parfaitement dimensionnés pour la simulation) est intégrée dans l'infobulle (tooltip / survol) du bandeau.

* **Composants Détectés** : Processeur (cœurs physiques, threads, fréquence), Carte Graphique (nom simplifié, VRAM totale dédiée), RAM système (taille, fréquence MHz et certification XMP/EXPO), SSD NVMe (lecteur MSFS et espace libre), débit réseau et latence ping, casques VR détectés (Pimax Crystal, Quest, SteamVR).
* **Bascule d'Écran en Un Clic** : Si vous possédez plusieurs écrans (ex. `DISPLAY1 (180 HZ)` et `DISPLAY2 (165 HZ)`), un simple clic sur la pilule de l'écran cible :
  1. Active cet écran comme moniteur principal de référence pour MSFS.
  2. Calcule la cible 1/2 Sync exacte (ex. 90 FPS pour 180 Hz, 82 FPS pour 165 Hz, 72 FPS pour 144 Hz, 60 FPS pour 120 Hz).
  3. Met à jour instantanément la valeur `TargetFrameRate` dans votre `UserCfg.opt`.
  4. Règle la cadence du Smart LOD en un seul geste, sans redémarrage.

> 📸 **ENCART CAPTURE D'ÉCRAN N°9 : Fenêtre « MY RIG » (System Optimizer & Hardware Specs)**
> ```text
> [ EMPLACEMENT CAPTURE D'ÉCRAN N°9 ]
> • Écran à capturer : Fenêtre "MY RIG & SYSTEM" avec ses deux onglets "System Optimizer" et "Hardware Specs".
> • Éléments visibles : Diagnostic des paramètres Windows/GPU (HAGS, Game Mode, Shader Cache), bandeaux "WINDOWS DIAGNOSIS" et "RIG ARCHITECTURE" avec pilules vertes OPTIMAL justifiées à droite, boutons "SETTINGS", et sélecteur d'écrans haute fréquence.
> • Cadrage recommandé : Fenêtre complète MY RIG (environ 700x520 px).
> • Légende : Figure 9 — Optimisation de l'environnement Windows / GPU et diagnostic matériel en temps réel adapté aux spécifications du rig.
> ```

---

## 10. Optimiseur Graphique MSFS & Gestion du UserCfg.opt

Le module de réglages graphiques expose directement l'intégralité des paramètres internes de votre simulateur, organisés en 3 environnements étanches :
* **Shared (Commun)** : Réglages généraux partagés (Résolution, Plein écran, Synchronisation V-Sync, NVIDIA Reflex).
* **2D Display** : Paramètres optimaux pour vol sur moniteur standard (DLSS, Frame Generation DLSSG/FSR3, limiteur de FPS 1/2 Sync).
* **VR Headset** : Profil dédié pour casque de réalité virtuelle, compatible avec le pont OpenXR Toolkit (OFXR).

Chaque ligne de paramètre affiche un badge d'évaluation en temps réel :
* `OPTIMUM` (Vert) : Réglage idéal offrant le meilleur compromis fluidité / fidélité visuelle.
* `SWEET SPOT` (Bleu ciel / Vert) : Fréquence d'images verrouillée sur un sous-multiple exact de votre écran.
* `ACCEPTABLE` (Ambre) : Réglage fonctionnel mais potentiellement coûteux en MainThread ou VRAM.

> 📸 **ENCART CAPTURE D'ÉCRAN N°10 : Matrice des Paramètres Graphiques MSFS & Badges Sweet Spot**
> ```text
> [ EMPLACEMENT CAPTURE D'ÉCRAN N°10 ]
> • Écran à capturer : Fenêtre "MSFS Graphics Settings" ouverte sur l'onglet "2D Display".
> • Éléments visibles : Les lignes Anti-Aliasing, Frame Generation, Max Frame Rate (avec son badge OPTIMUM 1/2 SYNC), boutons "Apply to MSFS" et "Restore Backup".
> • Cadrage recommandé : Vue de la table des paramètres graphiques (environ 850x600 px).
> • Légende : Figure 10 — Matrice d'optimisation graphique MSFS avec recommandations personnalisées et badges d'impact.
> ```

---

## 11. Panneau In-Game Cockpit (Toolbar HUD 2D & VR)

SceneryX intègre un panneau cockpit officiel déployable directement dans le bandeau supérieur de MSFS.

### Installation :
1. Rendez-vous dans les **Paramètres** de SceneryX (`roue crantée` en bas à droite).
2. Faites défiler jusqu'à la section **« In-Game Toolbar Panel »**.
3. Cliquez sur **« INSTALL »** : le package est immédiatement écrit dans votre dossier Community.
4. Lancez MSFS : l'icône SceneryX apparaît dans la barre d'outils du simulateur.

### Fonctionnalités dans le cockpit :
* Surveillance directe des FPS affichés et des FPS natifs hors interpolation.
* Latence du MainThread CPU en millisecondes pour anticiper les goulots d'étranglement.
* Ajustement instantané des curseurs TLOD / OLOD sans jamais quitter les commandes de votre appareil.

> 📸 **ENCART CAPTURE D'ÉCRAN N°11 : Le Panneau Toolbar SceneryX Actif dans le Cockpit MSFS**
> ```text
> [ EMPLACEMENT CAPTURE D'ÉCRAN N°11 ]
> • Écran à capturer : Vue cockpit MSFS (ex. A320 ou B737) avec le widget semi-transparent SceneryX ouvert.
> • Éléments visibles : Le mini-panneau HUD avec les jauges FPS, latence CPU MainThread, jauges TLOD/OLOD et interrupteurs de régulation.
> • Cadrage recommandé : Vue d'ensemble du cockpit avec focus sur le panneau toolbar (environ 1200x700 px).
> • Légende : Figure 11 — Panneau HUD SceneryX déployé directement dans le cockpit en plein vol.
> ```

---

## 12. Enregistreur Télémétrique & Rapports de Performance

Pour valider l'impact réel de vos réglages ou d'une nouvelle scène, SceneryX intègre une véritable **boîte noire télémétrique**.

1. Avant le décollage, cliquez sur **« Start Monitoring »** dans SceneryX ou directement depuis le panneau in-game.
2. Effectuez votre vol : décollage, croisière, approche et atterrissage.
3. À la coupure des moteurs, cliquez sur **« Stop & Save Report »**.
4. SceneryX génère un rapport interactif complet :
   * **Graphique temporel de fluidité** : courbe des FPS seconde par seconde avec ligne de flottaison du 1% Low.
   * **Temps de trame CPU MainThread** : repérage visuel des micro-gels lors du franchissement des zones photogrammétriques ou du survol des scènes lourdes.
   * **Bilan d'utilisation VRAM & RAM** : détection des pics de saturation mémoire.

> 📸 **ENCART CAPTURE D'ÉCRAN N°12 : Rapport Télémétrique de Vol & Graphiques de Fluidité**
> ```text
> [ EMPLACEMENT CAPTURE D'ÉCRAN N°12 ]
> • Écran à capturer : Fenêtre "Flight Performance Report" (Report Viewer).
> • Éléments visibles : Le graphique interactif des FPS avec la courbe verte, la barre de latence MainThread en ms, le tableau récapitulatif du vol et le badge de score global de fluidité.
> • Cadrage recommandé : Fenêtre de rapport complète (environ 900x650 px).
> • Légende : Figure 12 — Rapport télémétrique post-vol analysant la stabilité des FPS et les micro-saccades.
> ```

---

## 13. Paramètres, Caméras & Préférences Générales

Accessible via l'icône d'engrenage dans la barre d'outils inférieure, la modale des Paramètres centralise la configuration générale :

* **Répertoires de Scènes** : Chemins de vos dossiers Community et Official (détection automatique + ajout de dossiers personnalisés).
* **Répertoire GSX** : Emplacement des profils de sol FSDreamTeam.
* **Bouton d'Aide Contextuelle `?`** : Situé en haut à droite de la fenêtre des paramètres, ce bouton épuré sans bleu affiche une fiche d'aide claire et dédiée au menu actuel, sans jamais relancer le tutoriel général ni fermer votre fenêtre.
* **Réglages Caméra par Défaut** :
  * **Zoom de sélection aéroport** : Calibré par défaut sur **`8.0`** (parfait équilibre entre vue régionale et détails des pistes).
  * **Durée de transition caméra** : Calibrée par défaut sur **`1.1s`** pour des mouvements fluides sans effet de vertige.
* **Style de Navigation** : Choix entre *Sidebar Classique* ou *Hub Radial*.
* **Devise & Langue** : Choix entre EUR (€), USD ($), GBP (£) ou AUD (A$), et bascule entre Français, English, Deutsch et Español.

> 📸 **ENCART CAPTURE D'ÉCRAN N°13 : Fenêtre des Paramètres & Préférences Générales**
> ```text
> [ EMPLACEMENT CAPTURE D'ÉCRAN N°13 ]
> • Écran à capturer : Modale "Folder Locations & Settings" ouverte.
> • Éléments visibles : Les chemins de dossiers renseignés, le nouveau bouton d'aide discret "?", les curseurs de caméra réglés sur 8.0 et 1.1s, et les boutons de sauvegarde.
> • Cadrage recommandé : Modale des Paramètres centrée (environ 700x650 px).
> • Légende : Figure 13 — Fenêtre des paramètres généraux avec valeurs par défaut de caméras et sélecteur de mode.
> ```

---

## 🏁 En Résumé : Tableau Récapitulatif des 13 Captures d'Écran

Pour finaliser votre documentation imprimée ou exportée en PDF, voici la liste pense-bête des 13 visuels à capturer :

| N° | Sujet / Titre de la Capture | Emplacement dans SceneryX |
| :---: | :--- | :--- |
| **01** | Assistant d'Installation & Clé Gumroad | Installeur Windows `SceneryX_RC_v1.0.5_Setup.exe` |
| **02** | Mappemonde Globale & Statut de Collection | Écran principal au démarrage |
| **03** | Menu Hub Radial Tactique (ex. LPMA) | Clic sur un aéroport en mode Radial |
| **04** | Panneau de Filtres Multicritères | Sidebar gauche en Mode Classique |
| **05** | Gestionnaire d'Add-ons & Conflits Multi-Scènes | Modale des scènes disponibles sur un aéroport |
| **06** | Comparateur de Prix Payware en Direct | Fenêtre "Payware Scenery Search" |
| **07** | Tracé de Corridor SimBrief & Isolation de Route | Fenêtre "Flight Route Optimization" |
| **08** | Régulateur Dynamique Smart LOD | Fenêtre "Smart LOD & Auto FPS" |
| **09** | Diagnostic Matériel « MY RIG » & Sélecteur d'Écran | Carte MY RIG dans l'optimiseur |
| **10** | Matrice des Réglages Graphiques MSFS | Onglet 2D Display dans l'optimiseur |
| **11** | Panneau Toolbar HUD dans le Cockpit MSFS | Cockpit en vol dans MSFS |
| **12** | Rapport Télémétrique de Vol (Blackbox) | Fenêtre "Flight Performance Report" |
| **13** | Fenêtre des Paramètres & Caméras (8.0 / 1.1s) | Modale des Paramètres généraux |

---
*SceneryX © 2026 Sidestick Priority — Tous droits réservés.*
