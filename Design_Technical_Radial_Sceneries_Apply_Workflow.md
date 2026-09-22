# Design_Technical_Radial_Sceneries_Apply_Workflow

## 1. Contexte & Problématique

Dans le menu circulaire (Radial Menu) d'un aéroport, le panneau latéral **Sceneries** permet au joueur de choisir entre :
- Les variantes de scènes principales (**Available Addon Variants** et scène de base MSFS par défaut).
- Les correctifs et surcouches (**Available Fixes & Overlays**).

Auparavant :
1. Le clic sur une vignette de **Fix / Overlay** déclenchait immédiatement la modification sur le disque et dans `Content.xml` sans passer par le bouton **Apply**.
2. Le bouton **Apply** restait grisé (`disabled`) lorsqu'on modifiait uniquement l'état des Fixes & Overlays, car son calcul de changement (`hasPendingChange`) ne comparait que la variante de scène principale.
3. Le joueur ne pouvait donc pas préparer une configuration complète (variante principale + activation/désactivation des surcouches) et la valider d'un seul bloc via le bouton **Apply**.

---

## 2. Spécifications du Design Technique

### 2.1 Gestion d'état staged unifiée (`web/app.js`)

- **Objet d'état préparé (`stagedRadialScenerySelection`)** :
  L'état staged conserve désormais à la fois la variante principale ciblée (`target`) et un dictionnaire des états souhaités pour chaque correctif (`fixes[cleanName] = true | false`).
- **Fonction `stageRadialFixToggle(e, icao, cleanName)`** :
  - Intercepte le clic sur un Fix / Overlay dans l'extension radiale.
  - Bascule immédiatement l'interrupteur et la bordure dans l'interface visuelle (feedback instantané), mais **n'exécute aucune écriture sur disque**.
  - Si l'utilisateur re-clique pour remettre le fix dans son état d'origine sur le disque, l'entrée est retirée du dictionnaire staged.
- **Calcul du bouton Apply (`hasPendingChange`)** :
  - Compare la variante principale staged avec la variante active sur le disque (`hasVariantChange`).
  - Compare chaque fix présent dans `stagedRadialScenerySelection.fixes` avec son état réel sur disque (`hasFixesChange`).
  - Le bouton **Apply** s'illumine en cyan et devient cliquable dès que `hasVariantChange || hasFixesChange` est vrai.
  - Si toutes les options reviennent à leur état initial sur disque, le bouton redevient grisé et désactivé.

### 2.2 Exécution atomique Backend (`main.py`)

- **Nouvelle méthode API `apply_scenery_config(icao, target_folder_name="", fixes_json="{}")`** :
  - Regroupe en un seul appel l'ensemble des modifications demandées pour l'aéroport.
  - **Mise à jour synchronisée de `Content.xml`** :
    - Met à jour l'attribut `active="Activated"` ou `"UserDisabled"` pour chaque fix ciblé.
    - Met à jour le package de la scène principale si une variante est spécifiée.
  - **Gestion physique des fichiers** :
    - Active ou désactive les dossiers physiques / fichiers `.bgl` des scènes principales via `set_package_state_for_icao`.
    - Active (`enable_physical_package`) ou désactive (`disable_physical_package`) les packages de correctifs / surcouches sur disque.
  - **Mise à jour atomique du cache & persistances** :
    - Met à jour `fast_update_airport_cache` et synchronise le tableau `all_sources` de l'aéroport cible.
    - Met à jour le fichier `airports_output.json`.
    - Retourne l'objet aéroport rafraîchi `updated_airport` à l'interface Web.

---

## 3. Matrice de Validation

| Cas de Test | Action Utilisateur | Résultat Attendu |
| :--- | :--- | :--- |
| **Bascule d'un Fix seul** | Cliquer sur un switch de Fix / Overlay (vert -> éteint ou inversement). | Le switch bascule visuellement, le bouton **Apply** devient actif (cyan). Aucun changement n'est encore écrit sur disque. |
| **Annulation avant Apply** | Re-cliquer sur le même Fix pour le remettre dans son état initial. | Le switch revient à l'état initial, le bouton **Apply** redevient grisé. |
| **Bascule mixte** | Sélectionner une variante de scène ET basculer un ou plusieurs Fixes. | Les deux choix sont reflétés visuellement, le bouton **Apply** est actif. |
| **Clic sur Apply** | Cliquer sur le bouton **Apply** actif. | Le bouton passe à *"Applying..."*, l'API Python applique la variante et les fixes de manière atomique, un toast de confirmation s'affiche et l'UI se met à jour. |
