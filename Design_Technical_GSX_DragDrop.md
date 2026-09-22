# Design Technique : Résolution du Chargement Infini lors du Drag & Drop de Profils GSX

## 1. Contexte et Problème
Lors de l'utilisation du Drag & Drop pour installer un profil GSX (`.zip`, `.ini`, `.rar`, etc.) sur les dropzones de SceneryX :
- L'indicateur visuel se figeait indéfiniment sur `Installing profile...`.
- Le profil n'était jamais installé côté interface utilisateur et l'application ne réagissait plus aux actions suivantes.

## 2. Analyse des Causes Racines
1. **Dépassement de capacité du buffer IPC WebView2** :
   - `install_gsx_profile` dans `main.py` sérialisait la liste intégrale des aéroports (`airports`, ~19 450 éléments, soit plus de 27.75 Mo de JSON brut).
   - PyWebView renvoie les données à WebView2 via `ExecuteScriptAsync`. Sous Windows, Edge Chromium ne peut pas exécuter un script JavaScript de 28 Mo en une seule passe : l'évaluation échouait silencieusement et la Promise JS `await window.pywebview.api.install_gsx_profile(...)` restait bloquée indéfiniment.
2. **Absence de réinitialisation de la zone de drop** :
   - Le spinner dans `#radial-gsx-drop-text` n'était jamais réinitialisé si la modale de confirmation était fermée ou annulée, ou en cas d'erreur de lecture de fichier.
3. **Appel d'audit redondant** :
   - Un appel à `scan_gsx_audit()` était immédiatement relancé en JS après `install_gsx_profile`, alors que l'audit était déjà calculé.

## 3. Spécifications du Design
- **Optimisation Backend (`main.py`)** :
  - La synchronisation sur disque dans `installed_airports.json` est maintenue.
  - La valeur de retour est allégée : suppression du champ `airports` de 28 Mo, remplacé par l'objet aéroport mis à jour `airport` et `target_icao`.
  - La taille de la réponse passe de ~28 Mo à moins de 200 Ko, permettant une transmission IPC instantanée.
- **Gestion Frontend (`web/app.js`)** :
  - Introduction d'une fonction dédiée `resetRadialGsxDropzoneUI()`.
  - Encapsulation des flux d'installation dans des blocs `try...finally` pour garantir la restauration de l'état de la dropzone.
  - Prise en charge de l'annulation dans les modales pour restaurer la dropzone.
  - Rafraîchissement automatique des vues (modale radiale et panneau latéral Drawer).
