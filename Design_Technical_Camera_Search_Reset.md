# Design_Technical_Camera_Search_Reset

## 1. Contexte & Objectifs

Ce document détaille le design technique apporté à la gestion des caméras dans les Paramètres (Settings) et au comportement de recentrage de la caméra lors de la sortie du mode recherche.

Les objectifs principaux sont :
1. **Suppression du bouton redondant "Save Camera"** dans la section "Camera Settings" des préférences, remplacé par le bouton "Reset to Default" afin de s'appuyer sur le bouton global "Save" situé dans le pied de page du modal.
2. **Recentrage automatique de la caméra sur la "Default Startup Region" active** lors de l'effacement de la sélection dans le champ de recherche (croix ou effacement complet au clavier), uniquement lorsqu'un lieu était recherché.
3. **Réinitialisation totale par double-clic sur la carte en mode recherche**, reproduisant rigoureusement l'action d'effacement de la barre de recherche.

---

## 2. Spécifications & Architecture Technique

### 2.1 Refonte de l'en-tête Camera Settings (`web/index.html` & `web/app.js`)
- Le bouton `#btn-save-camera` a été supprimé pour éliminer toute redondance avec le bouton principal `saveSettings()` du modal.
- Le bouton `Reset to Default` (`resetCameraSettingsToDefault()`) est désormais positionné dans l'en-tête de la section sous forme de bouton stylisé avec icône de réinitialisation (`fa-rotate-left`), conforme au design de l'application.
- Un retour visuel par notification toast est affiché lors du clic pour confirmer la remise aux valeurs par défaut des réglages caméra.

### 2.2 Recentrage Caméra & Effacement de Recherche (`web/app.js`)
- **Nouvelle fonction `resetCameraToStartupRegion()`** :
  - Identifie la région de démarrage active configurée dans les paramètres utilisateur (`currentSettings.camera_startup_region`).
  - Si une région valide est configurée (`weurope`, `eeurope`, `namerica`, etc.), anime la caméra (`map.flyTo`) vers ses coordonnées et son niveau de zoom définis dans `REGION_VIEWPORTS`.
  - Si la région est `world` ou par défaut, anime vers la vue globale mondiale (`[25.0, 10.0]`, zoom `3.0`).
- **Évolution de `clearSearch(flyToDefaultStartup = true)`** :
  - Détecte si le mode recherche était actif (`wasSearchActive`).
  - Réinitialise le champ de recherche, masque le bouton de fermeture `#clear-search`, et retire le focus (`blur()`).
  - Ferme les menus radiaux (`closeAirportRadialMenu()`, `closeFilterRadialMenu()`) et les modals d'aéroports / compagnies ouverts.
  - Quitte le mode pays (`exitCountryMode(false)`) si un pays était sélectionné.
  - Réinitialise tous les filtres aux valeurs par défaut (`resetAllFiltersToDefault(true)`) et actualise l'affichage des aéroports (`filterAirports()`).
  - Recale la caméra via `resetCameraToStartupRegion()` si le mode recherche était actif.
- **Support de l'effacement manuel au clavier (`debouncedFilterAirports`)** :
  - Mémorise `previousSearchValue`. Si la saisie passe d'une chaîne non vide à une chaîne vide (par ex. touche Retour arrière ou suppression), `clearSearch(true)` est automatiquement exécuté.

### 2.3 Double-Clic sur la Carte en Mode Recherche (`web/app.js`)
- Les gestionnaires d'événements `dblclick` (sur le canevas Leaflet neutre et sur les polygones de pays GeoJSON) vérifient si le mode recherche est actif (`searchInp.value.trim().length > 0` ou pays sélectionné).
- Si le mode recherche est actif : interception immédiate et appel de `clearSearch(true)`. Tout est réinitialisé exactement comme lors d'un clic sur la croix du champ de recherche.
- Si le mode recherche n'est pas actif : maintien du comportement standard de double-clic (recadrage simple selon la vue par défaut sans altération des filtres du panneau latéral).

---

## 3. Matrice de Validation

| Cas de Test | Action | Résultat Attendu |
| :--- | :--- | :--- |
| **Bouton Reset Camera** | Ouvrir Settings > Camera Settings > cliquer sur "Reset to Default". | Valeurs remises à 'world', 6.0, 0.8s + toast de confirmation. Bouton Save Camera absent. |
| **Effacement via la Croix** | Taper "LEPA" (ou nom de pays) > appuyer sur Entrée > cliquer sur la croix. | Recherche effacée, filtres réinitialisés, caméra recentrée sur la Default Startup Region. |
| **Effacement via Backspace** | Taper "LFPG" > effacer avec Retour arrière jusqu'à ce que le champ soit vide. | Dès que le champ devient vide, déclenchement de `clearSearch(true)` et recentrage caméra. |
| **Double-clic en Mode Recherche** | Taper une recherche > double-cliquer n'importe où sur la carte. | Reset complet identique au clic sur la croix (barre vidée, filtres reset, caméra recentrée). |
| **Double-clic Hors Recherche** | Aucun texte dans la recherche > double-cliquer sur la carte. | Recentrage caméra sans écraser les filtres manuels du volet latéral. |
