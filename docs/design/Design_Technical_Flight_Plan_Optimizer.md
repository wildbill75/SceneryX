# Design Technique : Optimisation de Plan de Vol et Isolation des Aéroports

## 1. Vue d'ensemble du Système

Le module d'optimisation de plan de vol de SceneryX permet de préparer Microsoft Flight Simulator (2024 et 2020) pour un vol spécifique (ex: départ, arrivée, dégagements) en isolant uniquement les scènes nécessaires et en désactivant toutes les autres scènes d'aéroports afin de maximiser les performances (FPS, RAM, VRAM) et d'éliminer les conflits.

---

## 2. Architecture de Désactivation Hybride (MSFS 2024 & 2020)

### 2.1 Le Défi Technique de MSFS 2024
Dans MSFS 2024, le simulateur emploie un double mécanisme de gestion des packages :
1. **Le registre VFS tiers `LocalCache\ThirdBuk\Content.xml`** :
   Contrairement à MSFS 2020 qui s'appuyait principalement sur `LocalCache\Content.xml`, MSFS 2024 maintient son registre dynamique de packages Community et Marketplace dans `ThirdBuk\Content.xml`. Tout package y figurant avec `active="Activated"` est instancié par le moteur.
2. **L'auto-découverte des dossiers de `Community`** :
   Si un dossier est renommé avec le suffixe `.disabled` sur le disque mais que ses fichiers internes `manifest.json` et `layout.json` restent intacts, MSFS 2024 analyse le dossier, en déduit un package virtuel (ex: `communityfs24-mon-aeroport.disabled`) et l'ajoute automatiquement en tant que package `Activated` dans `ThirdBuk\Content.xml`.

### 2.2 La Solution de Conception : Double Verrouillage
Pour garantir une désactivation étanche et 100% fonctionnelle :
1. **Verrouillage Physique (VFS & Disque)** :
   - Via `disable_physical_package(path)` :
     - Le dossier dans `Community` reçoit le suffixe `.disabled`.
     - Les fichiers vitaux `manifest.json` et `layout.json` sont renommés en `.disabled`.
     - Sans `manifest.json`, le scanner VFS de MSFS 2024 ignore totalement le dossier et ne génère aucune entrée parasite.
2. **Verrouillage Logique (Content.xml & ThirdBuk\Content.xml)** :
   - Via `update_msfs_content_xml(...)` :
     - Synchronisation simultanée sur `LocalCache\ThirdBuk\Content.xml` et `LocalCache\Content.xml`.
     - Inscription de l'état `active="UserDisabled"` pour tous les packages d'aéroports hors du plan de vol.
     - Prise en charge des variantes de préfixes (`communityfs24-`, `communityfs20-`, `fs24-`, `fs20-`).
     - Nettoyage des balises temporaires orphelines se terminant par `.disabled` lors de la restauration.

---

## 3. Préservation et Protection des Utilitaires

Certains packages présents dans `Community` ne sont pas des scènes d'aéroports et ne doivent sous aucun prétexte être désactivés lors d'une optimisation de vol :
- Utilitaires généraux et panneaux : `autofps`, `beyondatc`, `toolbar`, `simbridge`, `fsuipc`, `mobiflight`, `gsx`, `sayintentions`, `chaseplane`, `p42-util`, `fsrealistic`, `raas`, `wwtwasm`, `simbrief`, `fsipanel`.
- Avions et flottes de livrées : `aircraft`, `livery`, `liveries`, `fleet`.
- Bibliothèques de modèles et trafic : `modellib`, `commonlibrary`, `projectairports`, `genericairports`, `navdata`, `traffic`, `gaist`.

Le filtre de sélection n'intervient que sur les dossiers confirmés comme scènes d'aéroports par la cartographie BGL issue du scan (`folder_to_icaos` et `third_party_airport_pkgs`).

---

## 4. Cycle de Vie : Optimisation et Restauration

```mermaid
sequenceDiagram
    autonumber
    actor Pilot as Pilote
    participant UI as SceneryX UI
    participant Opt as Flight Optimizer
    participant Disk as Disque (Community)
    participant XML as Content.xml & ThirdBuk

    Pilot->>UI: Clique sur "Optimize for Flight" (ICAO A -> B)
    UI->>Opt: optimize_flight_mode(keep_icaos)
    Opt->>Disk: disable_physical_package() sur aéroports hors vol
    Note over Disk: Renomme dossier.disabled + manifest.json.disabled
    Opt->>XML: Inscription active="UserDisabled"
    Note over XML: Mise à jour Content.xml & ThirdBuk/Content.xml
    Opt-->>UI: Confirmation et mise à jour de l'inventaire

    Pilot->>UI: Clique sur "Restore All Sceneries"
    UI->>Opt: restore_all_sceneries()
    Opt->>Disk: enable_physical_package()
    Note over Disk: Rétablit dossier + manifest.json
    Opt->>XML: Rétablit active="Activated" & purge balises .disabled
    Opt-->>UI: Inventaire complet rétabli
```
