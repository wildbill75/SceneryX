# Design_Technical_GSX_Sync_Persistence.md

## 1. Objectif du Design
Ce document décrit la synchronisation bidirectionnelle et la persistance de l'état des profils GSX entre le système de fichiers (`%APPDATA%\Virtuali\GSX\MSFS`), la base de données locale (`installed_airports.json`) et l'interface utilisateur SceneryX (Modal de Détails d'aéroport, Modal de liste d'audit GSX, et Tiroir latéral).

## 2. Problématique constatée
1. **Désynchronisation lors de la suppression / désactivation** :
   - Lorsque l'utilisateur désactivait ou supprimait un profil GSX (`LEPA.ini`) depuis la liste d'audit globale, le fichier était supprimé ou renommé sur le disque, mais `installed_airports.json` conservait l'entrée périmée (`has_gsx_profile: true`, `gsx_profile_filename: "LEPA.ini"`).
   - Dans le frontend, les propriétés `ap.gsx_profile_filename` et `currentRadialAirport.gsx_profile_filename` n'étaient pas purgées.
   - Lorsque `renderRadialGsx` s'exécutait, l'absence de profil dans `window.gsxAuditData.by_icao[ap.icao]` provoquait un fallback aveugle vers `else if (ap.has_gsx_profile)`, recréant artificiellement un badge `MATCH` avec l'ancien fichier `LEPA.ini`.
   - De plus, `closeAirportRadialMenu(keepModals=true)` réinitialisait `currentRadialAirport = null` de manière inconditionnelle, déconnectant le modal de détails affiché des mises à jour réactives.

2. **Désynchronisation lors d'une installation forcée** :
   - Lorsqu'un profil incompatible (`MISMATCH_VERSION`, ex: `lepa-n5ye8q.ini`) était déposé et installé de force, l'affichage de l'aéroport ne reflétait pas immédiatement le nouveau profil ni le badge `MISMATCH VERSION` à cause des fallbacks caducs et du cycle de vie du modal de détails.

## 3. Architecture du Design

### A. Backend (`main.py`)
- **Méthode unifiée `sync_airport_gsx_in_json(icao, has_profile, filename, file_path)`** :
  - Met à jour de façon atomique et synchrone `installed_airports.json` (à la fois dans `%APPDATA%\SceneryX` et dans le répertoire de travail si présent).
  - Si aucun profil actif ne subsiste : `has_gsx_profile = False`, et suppression systématique de `gsx_profile_filename`, `gsx_ini_file` et `gsx_profile_path`.
  - Appelé systématiquement par `delete_gsx_profile`, `disable_gsx_profile`, `enable_gsx_profile`, `delete_all_disabled_gsx_profiles`, `install_gsx_profile` et `check_airport_gsx_status`.

### B. Frontend (`web/app.js`)
- **Fonction unifiée `syncAirportGsxState(icao, options)`** :
  - Synchronise simultanément `allAirportsData`, `currentRadialAirport`, `selectedAirport` et le cache des marqueurs Leaflet.
  - Nettoie complètement les propriétés (`delete ap.gsx_profile_filename`, `delete ap.gsx_ini_file`, `delete ap.gsx_profile_path`) dès que le profil est supprimé ou inactif.
  - Déclenche immédiatement le réaffichage réactif des composants actuellement ouverts (`renderRadialGsx`, `renderRadialAirportDetails`, `renderDetails`).
- **Correction des conditions de fallback dans `renderRadialGsx(ap)`** :
  - Lorsque `window.gsxAuditData && window.gsxAuditData.by_icao` est disponible, l'absence de l'ICAO dans `by_icao` signifie de manière définitive qu'aucun profil n'est installé (`status = 'NONE'`).
  - Le fallback vers `status = 'MATCHED'` n'est autorisé que pendant le démarrage initial avant la toute première exécution de l'audit GSX.
- **Préservation de `currentRadialAirport`** :
  - `closeAirportRadialMenu(keepModals)` ne réinitialise `currentRadialAirport = null` que si `keepModals` est faux (`!keepModals`).
  - `radial-details-modal` conserve l'ICAO actif via son attribut `data-icao`.

## 4. Plan de Validation
1. Lancer l'audit sur `LEPA` et vérifier que le profil actif `lepa-n5ye8q.ini` est correctement identifié en `MISMATCH VERSION`.
2. Tester la suppression de profil : s'assurer que le modal de détails passe immédiatement à `NONE` sans conserver de reliquat de fichier.
3. Tester l'installation de profil : déposer un fichier et vérifier que le nom du fichier et son statut de correspondance (`MATCH` ou `MISMATCH VERSION`) sont instantanément synchronisés et affichés.
4. Recompiler l'exécutable `SceneryX.exe` via `python build_onefile.py` et valider les modifications.
