# Design_Technical_Settings_Folder_Names_Lock

## 1. Contexte & Problématique

Dans les Préférences (Settings), la liste des répertoires de scènes configurés (**MSFS SCENERY PATHS**) affichait pour chaque élément un champ texte modifiable (`<input type="text">`) contenant le nom du dossier :
- Chemins par défaut détectés (ex: `MSFS 2024 - StreamedPackages`, `MSFS 2024 - Official2020`, `MSFS 2024 - Official2024`).
- Chemins personnalisés ajoutés manuellement (ex: `Path_Test`).

Ce champ textuel permettait à l'utilisateur de cliquer dessus, de modifier le nom et de le renommer arbitrairement. Cette possibilité :
- Créait des ambiguïtés d'identification des répertoires du simulateur.
- Pouvait altérer la cohérence des libellés système et des configurations personnalisées.

---

## 2. Spécifications du Design Technique

### 2.1 Verrouillage de l'intitulé dans l'UI (`web/app.js`)

- **Suppression du champ de saisie (`<input>`)** :
  Le champ d'édition textuelle au-dessus du chemin a été supprimé au profit d'un libellé statique propre (`<span>`) stylisé en cyan bold :
  ```html
  <div class="flex items-center justify-between pb-0.5 select-none">
      <span class="text-xs font-bold text-cyan-400 tracking-wide truncate" title="${escapeHtml(item.name || 'MSFS Scenery Path')}">
          ${escapeHtml(item.name || 'MSFS Scenery Path')}
      </span>
  </div>
  ```
- **Suppression du curseur et des bordures d'édition** :
  Aucune bordure inférieure, aucun curseur de texte et aucune zone d'édition ne sont désormais présents. Le texte est en outre marqué `select-none` pour garantir un aspect professionnel de badge de section.
- **Suppression de `updatePathName`** :
  La fonction de renommage manuel a été complètement neutralisée.

### 2.2 Gestion automatique des noms de dossiers

- **Pour les dossiers officiels / par défaut** :
  Les noms officiels restent scellés et inchangés (`MSFS 2024 - Community`, `MSFS 2024 - Official2024`, etc.).
- **Pour les dossiers personnalisés (Custom Paths)** :
  - Lors de l'ajout via `+ Add Path`, le nom est automatiquement extrait du dernier segment du répertoire sélectionné sur le disque (ex: `Path_Test`).
  - Lors d'un changement de répertoire via le bouton de navigation (`browsePathFolder`), le libellé se synchronise automatiquement avec le nouveau dossier choisi.

---

## 3. Matrice de Validation

| Cas de Test | Action Utilisateur | Résultat Attendu |
| :--- | :--- | :--- |
| **Dossiers par défaut** | Tenter de cliquer ou d'éditer l'intitulé d'un dossier officiel (`MSFS 2024 - Official2020`). | Aucun champ de saisie n'apparaît, le libellé est figé et non modifiable. |
| **Dossiers personnalisés** | Tenter de cliquer ou d'éditer l'intitulé d'un dossier custom (`Path_Test`). | Le libellé est figé, aucun curseur ou bordure d'édition. |
| **Ajout d'un chemin custom** | Cliquer sur `+ Add Path` et sélectionner un dossier `D:\Sceneries\MyAirports`. | La ligne est créée avec le label `MyAirports` en lecture seule non éditable. |
| **Parcourir un dossier custom** | Cliquer sur l'icône dossier pour pointer vers `D:\Sceneries\OtherAirports`. | Le chemin est mis à jour et le label s'actualise automatiquement en `OtherAirports` sans permettre la saisie manuelle. |
