# Audit Détaillé & Spécifications de Design : Synchronisation 1-Clic SimBrief (SceneryX v1.0.0)

## 1. État des Lieux & Diagnostic de l'Existant

### 1.1 Backend Python (`main.py`)
- **Existant :** La méthode `Api.fetch_simbrief(identifier)` (l. 844–932) est déjà codée.
  - Elle interroge l'API XML/JSON publique de SimBrief : `https://www.simbrief.com/api/xml.fetcher.php?username={id}&json=1` (ou `userid={id}`).
  - Elle extrait : `origin`, `destination`, les `alternates` (1 à 4), le `flight_number`, l'`aircraft` et la `route`.
  - Elle enregistre `simbrief_username` et `simbrief_userid` dans `settings.json`.
- **Points d'amélioration identifiés :**
  - **Détails de route Navlog :** L'API SimBrief renvoie également le tableau `navlog.fix` contenant les coordonnées GPS précises de chaque waypoint de la route. L'exploiter permettrait un corridor parfaitement calqué sur la route ATC réelle au lieu d'une ligne de grand cercle théorique.
  - **Gestion réseau & Timeout :** Sécuriser le timeout à 6 secondes avec retour JSON explicite en cas d'absence de connexion Internet.

### 1.2 Frontend Web (`app.js` & `index.html`)
- **Déficit constaté dans l'interface actuelle :**
  - Lors de la récente refonte des paramètres (Settings), les champs d'entrée (`#sb-username-input` et `#sb-userid-input`) ont été omis du modal.
  - L'ancienne modale `#simbrief-modal` était conçue comme un écran séparé, non connecté au nouveau bandeau flottant dynamique (`#flight-planning-banner`).
  - Aucun point d'entrée direct SimBrief n'est actuellement visible dans l'en-tête ni dans le bandeau de vol.

---

## 2. Design Idéal & Expérience Utilisateur Cible (Produit Payant)

### 2.1 Configuration dans les Paramètres (Settings)
- **Nouvelle Section dédiée :** *"SimBrief Integration"* (avec icône SimBrief / Cloud ambre).
- **Champs & Contrôles :**
  - Champ de saisie : **SimBrief Username ou Pilot ID**.
  - Bouton *"Test & Link Account"* : interroge immédiatement SimBrief pour valider l'identifiant et afficher le statut (ex: *"✓ Connecté : Pilot ID 123456"*).
  - Option *"Auto-include Alternates"* (case à cocher cochée par défaut) : préserve automatiquement les scènes des aéroports de dégagement dans l'isolation.

### 2.2 Point d'Entrée 1 : Dans le Bandeau Flottant de Vol (`flight-planning-banner`)
- Comme illustré sur la capture fournie par l'utilisateur :
  - Actuellement, le bandeau affiche : `FLIGHT SCENERY OPTIMIZER | [LESU] -> [----] | Click an airport to set Destination | Exit`.
  - **Ajout stratégique :** Un bouton compact **"Sync SimBrief"** (ambre avec icône cloud/avion) inséré dans le bandeau.
  - En cliquant dessus :
    1. Si le username SimBrief est déjà configuré : SceneryX récupère instantanément le dernier vol.
    2. Si le vol SimBrief a pour départ `LESU`, il remplit automatiquement l'arrivée (ex: `LFPO`) et les dégagements.
    3. Si aucun vol ne correspond ou si l'utilisateur veut synchroniser l'ensemble du vol SimBrief, il charge le départ et l'arrivée directement.

### 2.3 Point d'Entrée 2 : Bouton Global 1-Clic dans l'En-tête Principal (Header)
- Un bouton d'action directe dans l'en-tête de la carte (à côté du carrousel de stats ou dans les contrôles de navigation) : **"Import SimBrief OFP"**.
- **Le flux magique en 1 clic :**
  1. Le pilote génère son vol sur SimBrief (sur son navigateur ou sa tablette).
  2. Il clique sur *"Import SimBrief OFP"* dans SceneryX.
  3. SceneryX ouvre immédiatement le bandeau de vol, charge `Origine ➔ Destination`, active le tracé du corridor avec les aéroports de dégagement, et propose d'optimiser le simulateur.
  4. Temps de manipulation pour l'utilisateur : **moins de 2 secondes**.

---

## 3. Matrice des Cas Limites & Résilience Industrielle

| Cas de figure | Comportement SceneryX attendu |
| :--- | :--- |
| **Aucun compte SimBrief configuré** | Modale concise guidant l'utilisateur avec un lien direct vers SimBrief et un champ de saisie immédiat sans le perdre. |
| **Identifiant inconnu / Erreur de frappe** | Alerte claire : *"Compte SimBrief introuvable. Veuillez vérifier votre Username ou Pilot ID."* |
| **Aucun plan de vol actif (OFP non généré)** | Alerte : *"Aucun vol actif généré sur SimBrief. Veuillez générer un vol sur simbrief.com puis réessayer."* |
| **Aéroport hors de la base de données MSFS** | Notification douce : l'aéroport est pris en compte pour le tracé mais SceneryX indique qu'aucune scène tierce n'est installée pour cette plateforme. |
| **Coupure réseau / SimBrief indisponible** | Timeout maîtrisé (6s) sans figer l'interface, notification d'avertissement explicite. |
