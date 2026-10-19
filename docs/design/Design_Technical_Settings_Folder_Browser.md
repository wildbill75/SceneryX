# Design_Technical_Settings_Folder_Browser

## 1. Contexte & Problématique

Lors de la gestion des répertoires dans les Préférences (Settings), qu'il s'agisse des scènes personnalisées (`scan_paths`) ou du répertoire des profils GSX (`cfg-gsx-path`), deux comportements altéraient l'expérience utilisateur :

1. **Absence d'affichage des fichiers dans la boîte de dialogue de sélection de dossier** :
   Dans les répertoires contenant uniquement des fichiers (sans sous-dossiers), Windows affichait le message *"Aucun élément ne correspond à votre recherche"*, masquant la totalité des fichiers présents et donnant l'impression trompeuse d'un dossier vide.
2. **Workflow du bouton "+ Add Path" et visibilité de l'élément créé** :
   Le clic sur `+ Add Path` créait immédiatement une ligne statique par défaut au bas de la liste sans ouvrir le sélecteur de dossier Windows. De plus, lorsque la liste comportait plusieurs chemins, le nouvel élément restait caché sous la zone de défilement sans que l'ascenseur ne descende pour le mettre en évidence.

---

## 2. Spécifications du Design Technique

### 2.1 Backend Python (`main.py`)

- **Affichage des fichiers dans la boîte de dialogue de dossier (`OpenFolderDialog`)** :
  - Par défaut dans `pywebview.platforms.winforms`, le filtre de sélection de dossier était configuré sur `'Folders|\n'`. Ce filtre masquait tous les fichiers classiques dans l'interface Windows `IFileDialog`.
  - Application d'un patch dynamique au démarrage :
    ```python
    try:
        import webview.platforms.winforms as wf
        if hasattr(wf, 'OpenFolderDialog'):
            wf.OpenFolderDialog.foldersFilter = 'All Files (*.*)|*.*'
    except Exception:
        pass
    ```
  - Dans la méthode `browse_folder(self, initial_directory="")` : si l'utilisateur clique sur un fichier à l'intérieur du dossier cible, `browse_folder` résout automatiquement `os.path.dirname(selected)` pour retourner le dossier conteneur valide.

- **Résolution du répertoire initial** :
  - Validation du chemin fourni (`normpath`, `isdir`).
  - Remontée d'arborescence vers le premier parent valide si le chemin exact n'existe pas.
  - Conversion systématique en chemin absolu (`os.path.abspath`) avec lettre de lecteur.

### 2.2 Frontend JavaScript & HTML (`web/app.js` & `web/index.html`)

- **Refonte asynchrone de `addCustomPathRow()`** :
  - La fonction devient `async`. Dès le clic sur `+ Add Path`, elle ouvre immédiatement la boîte de sélection Windows `window.pywebview.api.browse_folder(defaultDir)`.
  - Si l'utilisateur annule la sélection, aucune entrée superflue n'est créée.
  - Dès la sélection d'un dossier valide :
    1. Le nom du dossier est extrait dynamiquement du chemin (ex: `MyCustomScenery`) et assigné comme label de l'élément.
    2. La nouvelle entrée est ajoutée aux `scan_paths` et le rendu HTML est régénéré (`renderSettingsPathsList()`).
    3. L'ascenseur du conteneur `#settings-paths-list` défile automatiquement et de manière fluide vers le bas (`scrollTo({ top: scrollHeight, behavior: 'smooth' })`).
    4. Un anneau de surbrillance cyan (`ring-2 ring-cyan-400`) est temporairement appliqué à la nouvelle ligne pendant 2 secondes pour guider visuellement l'utilisateur.

- **Bouton d'ouverture directe dans l'Explorateur Windows** :
  - Chaque chemin dispose d'une icône `fa-arrow-up-right-from-square` permettant d'ouvrir immédiatement le répertoire dans l'Explorateur Windows via `window.pywebview.api.open_folder(path)`.

---

## 3. Matrice de Validation

| Cas de Test | Action | Résultat Attendu |
| :--- | :--- | :--- |
| **Parcourir avec contenu visible** | Ouvrir un dossier contenant des fichiers (ex: bgl, textures, ini). | Les fichiers sont parfaitement visibles dans la boîte de dialogue au lieu du message *"Aucun élément ne correspond"*. |
| **Sélection par clic sur fichier** | Sélectionner un fichier ou valider le dossier. | Le chemin du dossier parent est correctement extrait et renvoyé à SceneryX. |
| **Clic sur "+ Add Path"** | Cliquer sur le bouton `+ Add Path`. | La boîte Windows "Select Folder" s'ouvre immédiatement. |
| **Annulation "+ Add Path"** | Annuler la boîte de dialogue sans choisir. | Aucune ligne parasite n'est ajoutée à la liste. |
| **Validation "+ Add Path"** | Choisir un dossier dans la boîte. | La nouvelle ligne est créée avec le nom du dossier, la liste défile vers le bas et la ligne s'illumine en cyan. |
| **Ouvrir dans l'Explorateur** | Cliquer sur l'icône d'accès externe à côté d'un chemin ou de GSX. | L'Explorateur Windows s'ouvre instantanément sur le dossier concerné. |
