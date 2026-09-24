# Design Technique : Synchronisation SimBrief 1-Clic dans SceneryX v1.0.1

## 1. Vue d'Ensemble & Objectifs
L'objectif de cette fonctionnalité est d'offrir une synchronisation fluide en un clic entre la plateforme de planification de vol **SimBrief (Navigraph)** et **SceneryX v1.0.1**.

Le pilote ne doit plus avoir à sélectionner manuellement son aéroport de départ et son aéroport d'arrivée sur la carte : un simple clic sur **"SimBrief"** charge instantanément le dernier plan de vol généré (OFP), trace le corridor de vol, protège les aéroports de dégagement (Alternates) et prépare l'isolation des scènes du simulateur.

---

## 2. Composants & Architecture

### 2.1 Section Paramètres (Settings Modal)
- **Localisation :** Section dédiée *"SimBrief Integration"* dans la modale `#settings-modal`.
- **Contrôles :**
  - Champ de saisie : `cfg-simbrief-id` (supporte indifféremment le Username SimBrief ou le Pilot ID numérique).
  - Bouton *"Link Account"* : déclenche `testAndLinkSimBriefAccount()`.
  - Badge de statut dynamique :
    - Non lié : badge gris *"NOT LINKED"*.
    - Vérification en cours : icône animée *"Connecting..."*.
    - Connecté : badge vert *"✓ Connected as [Username] (ID: [PilotID])"*.
- **Persistance :** Les champs `simbrief_username`, `simbrief_userid` et `simbrief_map` sont stockés dans `%APPDATA%/SceneryX/settings.json`.

### 2.2 Points d'Entrée Utilisateur
1. **Bouton 1-Clic dans la Barre d'Outils Inférieure (`#bottom-map-toolbar`) :**
   - Bouton ambre bien visible : `<button onclick="syncSimBriefFlightPlan()">` avec icône `fa-cloud-arrow-down` et libellé *"SimBrief"*.
2. **Bouton dans le Bandeau Flottant d'Optimisation (`#flight-planning-banner`) :**
   - Bouton d'accès rapide dans le bandeau de vol permettant de réactualiser ou d'importer le vol SimBrief à tout moment.

### 2.3 Flux d'Exécution (Execution Flow)
1. **Appel API :** La fonction `syncSimBriefFlightPlan()` vérifie les identifiants configurés.
   - Si absent : ouverture automatique des paramètres avec focus sur le champ SimBrief et toast explicatif.
   - Si présent : appel de `pywebview.api.fetch_simbrief(identifier)`.
2. **Traitement du Plan de Vol (OFP) :**
   - Résolution des objets aéroports dans `allAirportsData` pour l'Origine (`flight.origin.icao`), la Destination (`flight.destination.icao`) et les Dégagements (`flight.alternates`).
   - Activation automatique du mode de planification :
     - `isFlightPlanningMode = true`
     - `flightPlanningDeparture = depAirport`
     - `flightPlanningDestination = arrAirport`
     - `flightCorridorArrivalAirport = arrAirport`
     - `flightPlanningAlternates = [altAirports]`
3. **Mise à Jour Cartographique & Visuelle :**
   - Rendu immédiat du bandeau de vol : `updateFlightPlanningBannerUI()`.
   - Tracé du corridor géodésique : `renderFlightCorridor()`.
   - Ajustement de la caméra de la carte (`map.fitBounds`) englobant le départ, l'arrivée et les dégagements.
   - Notification toast d'information complète avec le numéro de vol et l'appareil.

### 2.4 Protection des Aéroports de Dégagement (Alternates)
- Les aéroports alternats récupérés dans l'OFP sont automatiquement inclus dans la liste des scènes préservées lors de l'isolation du mode `CORRIDOR` ou `DIRECT`, garantissant qu'en cas de déroutement météo en vol, les scènes tierces des aéroports de secours restent 100% actives dans MSFS.
