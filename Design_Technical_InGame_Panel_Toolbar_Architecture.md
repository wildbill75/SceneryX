# Design Technique - Architecture du Toolbar Panel In-Game SceneryX

Ce document détaille le **Design** technique du module In-Game Toolbar Panel pour Microsoft Flight Simulator (MSFS 2020 et 2024), en prenant appui sur l'architecture éprouvée de **GateFinder** (`wildbill75-gatefinder`).

---

## 1. Contexte & Diagnostic des Échecs Antérieurs

Lors de la première itération, le panneau In-Game n'apparaissait pas dans la barre d'outils du simulateur pour plusieurs raisons structurelles identifiées après audit comparatif avec GateFinder :

1. **Type de Contenu dans le Manifeste (`manifest.json`)** :
   - *Ancienne version* : `"content_type": "MISC"` (les packages MISC sont ignorés par le gestionnaire de barre d'outils de MSFS).
   - *Design Révisé* : `"content_type": "UI"` (impératif pour l'enregistrement du bouton Toolbar).

2. **Absence du Package de Localisation (`en-US.locPak`)** :
   - MSFS nécessite la résolution des identifiants et chaînes de titre de panel via un dictionnaire de localisation (`en-US.locPak`). Sans cela, le loader UI ne peut pas étiqueter le widget dans la barre d'outils.

3. **Collision d'Identifiants avec AutoFPS** :
   - La première tentative réutilisait la structure générique `InGamePanel_HtmlWidgetPanel.spb` et l'ID `HTML_WIDGET_PANEL`.
   - Étant donné qu'un add-on AutoFPS (`autofps-html-widget-panel`) était déjà installé dans le dossier `Community` de l'utilisateur, MSFS supprimait ou écrasait l'entrée en double.

4. **Cycle de Vie CoherentGT (`TemplateElement`)** :
   - MSFS requiert l'héritage de `TemplateElement`, l'appel à `super.connectedCallback()`, l'enregistrement du custom element via `window.customElements.define("sceneryx-panel", SceneryXPanel)` et l'appel de terminaison `checkAutoload()`.

---

## 2. Reverse-Engineering du Format SPB (SimPropBinary)

Les fichiers `.spb` dans `InGamePanels/` définissent les métadonnées de barre d'outils (ID du panel, titre, URL HTML du widget, nom de l'icône).
L'analyse binaire a révélé que les chaînes de caractères dans les SPB de MSFS utilisent un chiffrement par flot (XOR) avec une séquence pseudo-aléatoire constante :

$$\text{Keystream} = [0\text{x}2a, 0\text{x}07, 0\text{x}2b, 0\text{x}31, 0\text{x}32, 0\text{x}5c, 0\text{x}63, 0\text{x}8e, 0\text{x}bf, 0\text{x}f1, 0\text{x}52, 0\text{x}b5, 0\text{x}48, 0\text{x}0c, \dots]$$

### Propriétés Chiffrées dans `InGamePanel_SceneryX.spb` :
1. **Panel ID** : `PANEL_SCENERYX_R` (17 octets)
2. **Title** : `SceneryX Panel` (15 octets)
3. **URL** : `html_ui/ingamePanels/SceneryX_Remote/SceneryX_Remote.html` (58 octets)
4. **Icon** : `SceneryX_R` (11 octets)

Grâce à cette extraction, le fichier `InGamePanels/InGamePanel_SceneryX.spb` a été généré de manière 100% native, sans dépendance externe à un compilateur SDK en cours de jeu.

---

## 3. Structure Finale du Package `sceneryx-ingame-panel`

```
sceneryx-ingame-panel/
├── manifest.json
├── en-US.locPak
├── layout.json
├── InGamePanels/
│   └── InGamePanel_SceneryX.spb
├── html_ui/
│   ├── icons/
│   │   └── toolbar/
│   │       ├── SceneryX_R.svg
│   │       ├── SceneryX_R-OFF.svg
│   │       ├── SceneryX.svg
│   │       ├── SceneryX-OFF.svg
│   │       ├── SceneryXPanel.svg
│   │       ├── SceneryXPanel-OFF.svg
│   │       ├── ICON_TOOLBAR_SCENERYX_R.svg
│   │       ├── ICON_TOOLBAR_SCENERYX_R-OFF.svg
│   │       ├── ICON_TOOLBAR_SCENERYX.svg
│   │       └── ICON_TOOLBAR_SCENERYX-OFF.svg
│   ├── Textures/
│   │   └── Menu/
│   │       └── toolbar/ (Mêmes SVGs pour compatibilité multi-versions)
│   └── ingamePanels/
│       └── SceneryX_Remote/
│           ├── SceneryX_Remote.html
│           ├── SceneryX_Remote.css
│           └── SceneryX_Remote.js
```

---

## 4. Fonctionnalités Intégrées dans le Panel

1. **Smart LOD Engine (Toggle ON / OFF)** :
   - Bascule interactive unifiée pour engager ou débrayer le moteur Smart LOD en vol sans ouvrir l'application externe.
   - Badge d'état dynamique affichant les valeurs en temps réel (`TLOD: 185 / OLOD: 150`).

2. **Impact FPS à Chaud & Frame Pacing** :
   - Affichage immédiat du FPS affiché (généré avec Frame Generation) et du FPS de base de la simulation.
   - Temps d'exécution Main Thread CPU en millisecondes avec pastille de fluidité (`FLUIDE`, `CHARGÉ`, `CRITIQUE`).
   - Courbe Sparkline sur 30 secondes avec calcul automatique du delta ($\Delta \text{ FPS}$).

3. **Télémétrie Mémoire & Enregistrement** :
   - Surveillance de la VRAM dédiée et du Rolling Cache.
   - Bouton de commande pour l'enregistreur de vol Blackbox SceneryX.
