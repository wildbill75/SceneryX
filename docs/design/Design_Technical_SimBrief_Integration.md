# Design Technique : Synchronisation SimBrief dans SceneryX v1.0.1

## 1. Vue d'Ensemble & Objectifs
L'objectif de cette fonctionnalité est d'offrir une synchronisation fluide en un clic entre la plateforme de planification de vol **SimBrief (Navigraph)** et **SceneryX v1.0.1**, dans une interface sobre, sobrement intégrée et fidèle à l'ergonomie sombre du logiciel.

Le pilote ne doit plus avoir à sélectionner manuellement son aéroport de départ et son aéroport d'arrivée sur la carte : un simple clic sur la position **"SimBrief"** dans le sélecteur de profil charge instantanément le dernier plan de vol généré (OFP), trace le corridor de vol, protège les aéroports de dégagement (Alternates) et prépare l'isolation des scènes du simulateur.

---

## 2. Composants & Architecture

### 2.1 Section Paramètres (Settings Modal)
- **Design Sobre & Discret :** Entièrement harmonisée avec le reste des paramètres (`GSX Profile Directory`, `Map Airport Labels`).
- **Contrôles :**
  - Titre épuré : `SIMBRIEF` (typographie standard slate-400 majuscule).
  - Champ de saisie : `cfg-simbrief-id` avec placeholder discret `"Pilot name or id"`.
  - Pas de bouton *"Link Account"* superflu : validation et liaison automatiques en arrière-plan sans bruit visuel.
  - Indicateur de statut chic et minimaliste : micro-point vert émeraude (`w-1.5 h-1.5`) avec libellé discret `Connected` directement intégré sur le bord droit interne du champ de saisie.
- **Persistance :** Les champs `simbrief_username` et `simbrief_userid` sont stockés dans `%APPDATA%/SceneryX/settings.json`.

### 2.2 Sélecteur de Profil à 3 Positions (Flight Planning Banner)
- **Intégration Harmonisée :** Le bouton SimBrief est directement intégré dans le sélecteur segmenté de profil `#fp-profile-toggle`, offrant désormais 3 positions homogènes :
  1. `[ SimBrief ]` : Importe / synchronise l'OFP actif, protège les aéroports de dégagement (*Alternates*) ainsi que les scènes du corridor.
  2. `[ En-Route ]` : Mode couloir géodésique standard préservant les scènes situées le long du trajet.
  3. `[ Direct ]` : Mode boost FPS maximal conservant uniquement les aéroports de départ et d'arrivée.
- **Style Visuel Unifié :** Style pilule identique pour les 3 boutons (actif : cyan profond avec ombre douce ; inactif : texte ardoise discret sur fond sombre). Aucune icône de nuage, aucune teinte ambrée parasite, aucun dégradé glass disproportionné.

### 2.3 Flux d'Exécution (Execution Flow)
1. **Appel API :** La fonction `syncSimBriefFlightPlan()` vérifie les identifiants configurés.
   - Si absent : ouverture automatique des paramètres avec focus sur le champ SimBrief et toast explicatif.
   - Si présent : appel de `pywebview.api.fetch_simbrief(identifier)`.
2. **Traitement du Plan de Vol (OFP) :**
   - Résolution des objets aéroports dans `allAirportsData` pour l'Origine (`flight.origin.icao`), la Destination (`flight.destination.icao`) et les Dégagements (`flight.alternates`).
   - Activation automatique du mode de planification avec profil `SIMBRIEF`.
3. **Mise à Jour Cartographique & Visuelle :**
   - Mise à jour du bandeau de vol : `updateFlightPlanningBannerUI()`.
   - Tracé du corridor géodésique : `renderFlightCorridor()`.
   - Ajustement de la caméra de la carte (`map.fitBounds`) englobant le départ, l'arrivée et les dégagements.
   - Notification toast discrète avec le numéro de vol et l'appareil.

### 2.4 Protection des Aéroports de Dégagement (Alternates)
- Les aéroports alternats récupérés dans l'OFP sont automatiquement inclus dans la liste des scènes préservées lors de l'isolation du mode `SIMBRIEF`, garantissant qu'en cas de déroutement météo en vol, les scènes tierces des aéroports de secours restent 100% actives dans MSFS.
