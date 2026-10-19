# Design Technique : Persistance de la Saisie Pays & Réinitialisation Recherche

## 1. Contexte & Problématique
Lorsqu'un utilisateur recherche un aéroport par son code ICAO, son nom ou sa ville et valide avec la touche `Entrée`, le texte saisi reste présent dans le champ de recherche (`#search-input`) et le bouton de réinitialisation croix (`#clear-search`) reste accessible pour annuler la recherche à tout moment.

Cependant, lorsqu'un utilisateur saisissait le nom d'un pays (ex. `france`, `allemagne`, `espagne`) et pressait `Entrée` :
1. `triggerSearchFocus()` détectait le pays via `COUNTRY_NAME_TO_ISO` et invoquait `toggleCountrySelection()`.
2. `toggleCountrySelection()` vidait inconditionnellement la valeur du champ (`searchInp.value = ''`) et masquait le bouton croix (`clearBtn.classList.add('hidden')`).
3. L'utilisateur voyait sa saisie s'effacer instantanément et ne disposait plus du bouton croix pour réinitialiser sa recherche.
4. Si `clearSearch()` était invoqué, il ne réinitialisait pas `selectedCountryCode`, maintenant le filtre géographique actif.

## 2. Architecture du Design

### A. Préservation de la saisie lors du focus pays
- Ajout du paramètre `keepSearchInput` dans `toggleCountrySelection(iso, countryName, layer, forceSelect = false, keepSearchInput = false)`.
- Lors de l'activation via la recherche clavier (`triggerSearchFocus`), `keepSearchInput` est positionné à `true` :
  - La valeur de `#search-input` est conservée intacte.
  - Le bouton croix `#clear-search` reste visible (`classList.remove('hidden')`).
  - Dans la capture d'état `preCountryModeFilters`, la recherche précédente est initialisée à vide afin d'éviter une réinjection intempestive de la chaîne lors d'une sortie future de mode.

### B. Réinitialisation unifiée via le bouton croix (`clearSearch`)
- Lorsque l'utilisateur clique sur la croix (`#clear-search`) :
  - Le champ `#search-input` est vidé (`value = ''`).
  - Le bouton croix est masqué (`classList.add('hidden')`).
  - Si un pays était sélectionné (`selectedCountryCode`), `exitCountryMode(false)` est immédiatement exécuté pour retirer le polygone de surbrillance violet, réinitialiser `selectedCountryCode` à `null` et restaurer les filtres d'origine.
  - La fonction `filterAirports()` est déclenchée, affichant à nouveau l'ensemble des scènes de la carte globale.

### C. Gestion dynamique lors de la saisie (`debouncedFilterAirports`)
- Si l'utilisateur efface manuellement le texte ou saisit un terme différent de l'ISO du pays actif, le mode pays est automatiquement désactivé sans friction pour rebasculer sur le filtrage global par défaut.
- Enrichissement de `COUNTRY_NAME_TO_ISO` avec les variantes francophones usuelles pour une détection immédiate.
