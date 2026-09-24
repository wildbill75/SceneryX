# Design Stratégique & Technique : Feuille de Route Commerciale SceneryX (Version Payante)

## 1. Vision Commerciale & Positionnement Marché

Pour positionner **SceneryX** comme un utilitaire payant incontournable (SimMarket, Flightsim.to, Aerosoft, Orbx) entre 15 € et 30 €, le produit doit dépasser le simple rôle de gestionnaire de scènes pour devenir un **Véritable Centre de Contrôle de Performance et de Gestion d'Écosystème MSFS**.

Le public cible (pilotes virtuels sur liners, GA, réseaux VATSIM/IVAO) achète deux valeurs clés :
1. **Le Gain de Performance / Zéro CTD** (FPS accrus, temps de chargement réduits de 50 à 70%, pas de Crash-to-Desktop).
2. **Le Confort & l'Automatisation Sans Risque** (aucun risque de corrompre le simulateur, synchronisation avec les outils du quotidien comme SimBrief).

---

## 2. Piliers d'Élévation Commerciale

### Pilier 1 : Solidité Industrielle du Code & Fiabilité Zéro Défaut
- **Gestionnaire de Points de Restauration Automatiques (Snapshot & Rollback)** :
  - Sauvegarde atomique horodatée de `Content.xml` et des états de scènes avant toute modification.
  - Bouton *"Restaurer l'état usine"* en un clic en cas de mise à jour du simulateur (Sim Update).
- **Écriture Atomique & Verrous Fichiers (Atomic File I/O)** :
  - Utilisation systématique de fichiers temporaires avec remplacement atomique (`os.replace`) pour interdire toute corruption de fichier JSON ou XML en cas de coupure de courant ou d'arrêt forcé.
- **Rapport de Diagnostic en 1 Clic (Customer Support Package)** :
  - Génération d'un fichier ZIP chiffré/anonymisé contenant les logs techniques, la version Windows/MSFS et l'état de l'index pour faciliter le support après-vente sans exposer de données personnelles.
- **Auto-Détection & Réparation de Base de Données** :
  - Vérification de l'intégrité de la base de données au démarrage et réparation silencieuse sans blocage.

---

### Pilier 2 : Polish Visuel & Expérience Utilisateur Premium (UI/UX)
- **Assistant d'Accueil Interactif (Onboarding Wizard)** :
  - Au premier lancement : détection automatique des dossiers MSFS, choix de la langue, vérification du dossier GSX et visite guidée interactive en 3 étapes.
- **Compatibilité 4K & Écrans Ultra-Larges (High-DPI)** :
  - Calibrage des polices vectorielles, marges et menus radiaux pour une netteté absolue du 1080p au 4K et 32:9.
- **Guide des Raccourcis Clavier & Aide Intégrée (`?` modal)** :
  - Affichage instantané d'une antisèche visuelle des touches rapides (Esc pour sortir, F pour recherche, etc.).
- **Indicateur de Santé du Simulateur (Sim Health Status)** :
  - Widget discret dans le bandeau indiquant le statut de MSFS (Fermé, En cours, Optimisé pour vol, Conflits détectés).

---

### Pilier 3 : Fonctionnalités à Haute Valeur Ajoutée (Features Vendeuses)

#### 🚀 A. Synchronisation 1-Clic SimBrief (La "Killer Feature")
- **Fonctionnement :** L'utilisateur entre son identifiant SimBrief.
- En cliquant sur *"Importer le vol SimBrief"* :
  - SceneryX récupère le dernier plan de vol (OFP) généré.
  - Détection automatique de l'Origine, de la Destination, de l'Aéroport de Dégagement (Alternate) et de la route.
  - Tracé automatique du corridor et activation de l'optimisation en **un seul clic**, sans aucune saisie manuelle.

#### 📊 B. Analyseur d'Espace Disque & Poids des Scènes (Disk Space Treemap)
- Les dossiers Community dépassent souvent 300 Go à 1 To.
- Tableau de bord visuel montrant la répartition du stockage par studio éditeur, par aéroport et par pays.
- Identification immédiate des scènes volumineuses peu utilisées.

#### 🎛️ C. Gestionnaire de Préréglages Régionaux (Presets Manager)
- En plus du vol point A ➔ point B, possibilité de sauvegarder des profils réutilisables :
  - *"VFR France"*
  - *"Transatlantique Long-Courrier"*
  - *"Événement VATSIM Allemagne"*
- Activation du profil sélectionné en 1 clic avant de lancer le simulateur.

#### 🔄 D. Système de Mise à Jour Automatique (Auto-Updater & Changelog)
- Détection discrète des nouvelles versions au démarrage.
- Affichage de la note de version (*Changelog*) et mise à jour transparente sans réinstallation complexe.

#### 🛡️ E. Détecteur de Conflits & Incompatibilités Sim Update
- Analyse des packages pour alerter le pilote sur les scènes connues pour provoquer des CTD avec la version active de MSFS 2024 / 2020.
