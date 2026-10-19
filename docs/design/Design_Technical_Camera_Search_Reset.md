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
  - Stoppe toute animation Leaflet en cours (`map.stop()`) pour prévenir les conflits de transitions.
  - Si une région valide est configurée (`weurope`, `eeurope`, `namerica`, etc.), anime la caméra (`map.flyTo`) vers ses coordonnées et son niveau de zoom définis dans `REGION_VIEWPORTS`.
  - Si la région est `world` ou par défaut, anime vers la vue globale mondiale (`[25.0, 10.0]`, zoom `3.0`).
- **Évolution de `clearSearch(flyToDefaultStartup = true)` & Persistance de Focus Pays** :
  - Détection multi-critères fiable de l'état de recherche actif (`wasSearchActive`), couvrant le texte résiduel, `selectedCountryCode`, `lastFocusedCountryCode`, `lastFocusedIcao`, et `previousSearchValue`.
  - Nettoyage du minuteur d'anti-rebond de recherche (`searchDebounceTimer`).
  - Réinitialise le champ de recherche, masque le bouton de fermeture `#clear-search`, et retire le focus (`blur()`).
  - Ferme les menus radiaux (`closeAirportRadialMenu()`, `closeFilterRadialMenu()`) et les modals d'aéroports / compagnies ouverts.
  - Quitte le mode pays (`exitCountryMode(false)`) si un pays était sélectionné.
  - Réinitialise tous les filtres aux valeurs par défaut (`resetAllFiltersToDefault(true)`) et actualise l'affichage des aéroports (`filterAirports()`).
  - Recale la caméra via `resetCameraToStartupRegion()` dès qu'une recherche ou sélection de pays/aéroport était active.
- **Support de l'effacement manuel au clavier (`debouncedFilterAirports`)** :
  - Mémorise `previousSearchValue` et conserve l'historique du focus (`lastFocusedCountryCode`).
  - Lors de la suppression graduelle (touches Retour arrière / Suppr) ou totale d'un nom de pays, évite la destruction prématurée de l'état de pays avant le déclenchement de `clearSearch(true)`.
  - Déclenche automatiquement `clearSearch(true)` dès que la saisie redevient vide.
- **Désélection directe par clic sur le pays ou touche Échap** :
  - Cliquer sur le polygone du pays actif pour le désélectionner (`toggleCountrySelection`) ou presser la touche `Échap` route directement vers `clearSearch(true)`, garantissant le retour à la vue de démarrage sélectionnée dans les options.

### 2.3 Double-Clic sur la Carte en Mode Recherche (`web/app.js`)
- Les gestionnaires d'événements `dblclick` (sur le canevas Leaflet neutre et sur les polygones de pays GeoJSON) vérifient si le mode recherche est actif (`searchInp.value.trim().length > 0`, `selectedCountryCode`, ou `lastFocusedCountryCode`).
- Si le mode recherche est actif : interception immédiate et appel de `clearSearch(true)`. Tout est réinitialisé exactement comme lors d'un clic sur la croix du champ de recherche.
- Si le mode recherche n'est pas actif : maintien du comportement standard de double-clic (recadrage simple selon la vue par défaut sans altération des filtres du panneau latéral).

---

## 3. Matrice de Validation

| Cas de Test | Action | Résultat Attendu |
| :--- | :--- | :--- |
| **Bouton Reset Camera** | Ouvrir Settings > Camera Settings > cliquer sur "Reset to Default". | Valeurs remises à 'world', 6.0, 0.8s + toast de confirmation. Bouton Save Camera absent. |
| **Recherche Pays - Effacement Croix** | Taper "France" > appuyer sur Entrée (caméra centrée sur la France) > cliquer sur la croix. | Recherche effacée, filtres reset, caméra recentrée immédiatement sur la vue active des options (ex: Western Europe). |
| **Recherche Pays - Effacement Backspace** | Taper "France" > Entrée > effacer au clavier lettre par lettre jusqu'à chaîne vide. | Champ vidé, mode pays quitté, recentrage automatique de la caméra sur la région de démarrage active. |
| **Recherche Pays - Clic Désélection** | Taper "France" > Entrée > cliquer sur le polygone France sur la carte. | Désélection complète, barre de recherche vidée, caméra recalée sur la région de démarrage active. |
| **Effacement via la Croix (Aéroports)** | Taper "LEPA" > appuyer sur Entrée > cliquer sur la croix. | Recherche effacée, filtres réinitialisés, caméra recentrée sur la Default Startup Region. |
| **Effacement via Backspace (Aéroports)** | Taper "LFPG" > effacer avec Retour arrière jusqu'à ce que le champ soit vide. | Dès que le champ devient vide, déclenchement de `clearSearch(true)` et recentrage caméra. |
| **Double-clic en Mode Recherche (Pays & Aéroports)** | Taper un pays ou aéroport > double-cliquer n'importe où sur la carte. | Reset complet identique au clic sur la croix (barre vidée, filtres reset, caméra recentrée). |
| **Double-clic Hors Recherche** | Aucun texte dans la recherche > double-cliquer sur la carte. | Recentrage caméra sans écraser les filtres manuels du volet latéral. |
