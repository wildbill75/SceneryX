# Design_Technical_Settings_Folder_Browser

## 1. Contexte & Problématique

Lors de la sélection d'un dossier dans les Préférences (Settings), qu'il s'agisse des répertoires de scènes personnalisées (`scan_paths`) ou du répertoire des profils GSX (`cfg-gsx-path`), le clic sur le bouton de navigation ouvrait systématiquement la boîte de dialogue Windows ("Select Folder") positionnée sur le **Bureau (Desktop)** de l'utilisateur, au lieu de s'ouvrir sur le chemin déjà configuré dans le champ texte.

### Causes identifiées
1. **Absence d'argument de répertoire dans l'API Python (`main.py`)** :
   La méthode `browse_folder(self)` n'acceptait aucun paramètre et invoquait directement `window.create_file_dialog(webview.FOLDER_DIALOG)` sans lui passer de répertoire initial (`directory=''`).
2. **Comportement par défaut de Windows / pywebview** :
   Lorsque `directory` est vide, `pywebview` sous Windows bascule sur `os.environ['HOMEPATH']` (qui vaut `\Users\<Nom>` sans lettre de lecteur `C:`). Ne pouvant résoudre ce chemin incomplet, l'API WinForms / IFileDialog bascule systématiquement par défaut sur le Bureau (`Desktop`).
3. **Absence d'action d'ouverture directe dans l'Explorateur Windows** :
   Les utilisateurs souhaitant simplement inspecter le contenu du dossier configuré devaient copier-coller manuellement le chemin dans Windows Explorer.

---

## 2. Spécifications du Design Technique

### 2.1 Backend Python (`main.py`)
- Évolution de la méthode `browse_folder(self, initial_directory="")` :
  - Accepte désormais un paramètre optionnel `initial_directory`.
  - Nettoie les guillemets et espaces éventuels du chemin transmis.
  - Valide l'existence du dossier via `os.path.normpath` et `os.path.isdir`.
  - Si le dossier exact n'existe pas (ex: saisie incomplète ou sous-dossier supprimé), remonte récursivement l'arborescence jusqu'au premier dossier parent existant.
  - Convertit impérativement le chemin en chemin absolu avec lettre de lecteur (`os.path.abspath`) pour garantir la compatibilité avec l'API Windows `IFileDialog`.
  - Transmet le chemin résolu au paramètre `directory` de `window.create_file_dialog(webview.FOLDER_DIALOG, directory=valid_dir)`.

### 2.2 Frontend JavaScript & HTML (`web/app.js` & `web/index.html`)
- **Navigation de dossier ciblée (`browsePathFolder` & `browseGsxFolder`)** :
  - Transmet la valeur textuelle actuelle du champ (ex: `C:\Users\...\AppData\Roaming\Virtuali\GSX\MSFS` ou le chemin de la ligne de scène cliquée) à `window.pywebview.api.browse_folder(currentPath)`.
  - La boîte de sélection s'ouvre désormais directement au cœur du dossier existant.
- **Ajout du bouton "Ouvrir dans l'Explorateur Windows"** :
  - Ajout d'une icône dédiée (`fa-arrow-up-right-from-square`) à côté de chaque bouton de navigation de dossier dans la liste des chemins de scènes et dans la section GSX.
  - Déclenche `openPathInExplorer(index)` ou `openGsxFolderInExplorer()`, appelant `window.pywebview.api.open_folder(path)` pour afficher immédiatement le dossier dans l'Explorateur de fichiers Windows.

---

## 3. Matrice de Validation

| Cas de Test | Action | Résultat Attendu |
| :--- | :--- | :--- |
| **Parcourir GSX** | Cliquer sur "Browse" à côté du champ GSX (`...\Virtuali\GSX\MSFS`). | La boîte "Select Folder" s'ouvre directement dans le dossier GSX, et non plus sur le Bureau. |
| **Parcourir Scènes** | Cliquer sur l'icône dossier à côté d'un chemin de scène existant (ex: Community). | La boîte "Select Folder" s'ouvre directement au sein de ce dossier Community. |
| **Ouvrir dans l'Explorateur** | Cliquer sur l'icône d'accès externe à côté d'un chemin ou de GSX. | L'Explorateur Windows s'ouvre instantanément sur le dossier concerné. |
| **Chemin inexistant / Nouveau** | Cliquer sur parcourir avec un chemin vide ou partiellement invalide. | La boîte s'ouvre sur le dossier parent valide le plus proche ou dans le répertoire utilisateur avec lettre de lecteur. |
