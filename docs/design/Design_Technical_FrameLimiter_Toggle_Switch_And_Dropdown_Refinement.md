# Design Technique : Refonte du Limiteur de Framerate, Suppression du "OFF" Redondant et Affichage de l'État Choisi en Gris

## 1. Contexte & Problématique

Dans l'architecture de configuration graphique de SceneryX, le réglage **Max Frame Rate** (en mode 2D Monitor et en mode VR Headset) dispose d'un sélecteur combiné :
1. Une zone de saisie / liste déroulante (combobox) permettant de sélectionner des paliers de framerate synchronisés avec les harmoniques de l'écran (ex. 60, 72, 80, 82, 90, 120 FPS).
2. Un commutateur à bascule (**Toggle Switch**) ON / OFF permettant d'activer ou de désactiver le limiteur global du pipeline graphique MSFS (`TargetFrameRate` / `FrameLimiter`).

### Dysfonctionnements Constatés
- **Redondance "OFF" :** La présence de l'option "OFF" dans la liste déroulante faisait doublon direct avec le switch ON/OFF adjacent.
- **Affichage textuel inopportun :** Lorsque le switch était basculé sur OFF, la boîte de saisie remplaçait le chiffre configuré par la mention textuelle `"OFF"` surmontée d'un curseur clignotant ambré, et le menu déroulant affichait l'élément `OFF [ACCEPTABLE] [CURRENT]`.
- **Perte visuelle de la cible :** L'utilisateur perdait la lisibilité de sa valeur cible (par exemple 82 FPS pour un écran 165 Hz ou 45 FPS pour un casque VR 90 Hz).

---

## 2. Principes du Design Retenu

Le design unifié repose sur les règles directrices suivantes :

1. **Suppression définitive du "OFF" dans les choix déroulants :**
   - La liste `fps_options` dans le moteur Python ne propose plus que des valeurs numériques positives :
     `["30", "36", "40", "45", "60", "72", "80", "82", "90", "120", "144", "165", "180", "240"]`.
   - Dans le frontend web, un filtre systématique retire toute occurrence de `'OFF'` des menus déroulants pour les paramètres régis par un switch binaire.

2. **Préservation et affichage de l'état choisi en gris ("en gris") :**
   - Lorsque le limiteur est désactivé (OFF), la boîte de saisie ne se vide pas et n'affiche jamais le mot "OFF". Elle affiche la valeur cible choisie (ex. `82` ou `45`), grisée avec le style Tailwind `text-slate-500 opacity-60`.
   - L'état mémorisé (`_lastActiveFps`) est préservé lors des transitions ON $\leftrightarrow$ OFF.
   - Si MSFS est initialement chargé avec `TargetFrameRate 0`, le moteur injecte la valeur harmonique cible détectée du matériel (`target_fps`, ex. 82 FPS pour 165 Hz) pour un affichage immédiat en gris.

3. **Badge de statut cohérent :**
   - En état OFF, le badge d'en-tête de carte bascule sur le libellé neutre `OFF` avec le style `bg-slate-700 text-slate-300 font-bold`.
   - L'attribution par défaut d'un badge vert `OPTIMUM` sur un limiteur inactif est neutralisée.

4. **Interaction fluide et activation automatique :**
   - Si l'utilisateur clique sur une valeur dans le menu déroulant ou saisit un nombre au clavier, le limiteur s'active automatiquement : le switch bascule sur ON (vert émeraude `bg-emerald-600`), le texte repasse en vert `text-emerald-400`, et la valeur est immédiatement transmise au fichier `UserCfg.opt`.
   - Si l'utilisateur clique sur le switch pour couper le limiteur, la valeur reste affichée en gris, le switch glisse à gauche sur fond ardoise (`bg-slate-700`), et la valeur `0` est appliquée dans `UserCfg.opt`.

---

## 3. Détail des Modifications Techniques

### 3.1 Backend Python (`flight_rig_optimizer.py`)
- **Options de framerate épurées :**
  ```python
  fps_options = ["30", "36", "40", "45", "60", "72", "80", "82", "90", "120", "144", "165", "180", "240"]
  ```
- **Gestion du label et de la couleur OFF dans `make_setting_item` :**
  ```python
  if clean_lbl in ["OFF", "INACTIVE", "DISABLED"]:
      clean_lbl = "OFF"
      color = "slate"
      rating = "acceptable"
  ```
- **Propriétés structurelles additionnelles :**
  Injection de `is_active` (`bool`) et `target_fps` (`int`) dans l'objet dictionnaire retourné pour chaque item de la matrice 2D et VR.

### 3.2 Frontend Web (`web/app.js`)
- **Calcul de `displayVal` :**
  ```javascript
  if (item.key === 'max_frame_rate') {
      const isOff = (item.is_active === false) || item.raw_value === '0' || item.value === '0' || String(item.value).toUpperCase() === 'OFF';
      const defaultTargetFps = (String(currentMsfsGraphicsMode || '2D').toUpperCase() === 'VR') ? '45' : '82';
      if (isOff) {
          displayVal = item._lastActiveFps || (item.target_fps ? String(item.target_fps) : '') || (item.raw_value && item.raw_value !== '0' ? item.raw_value : defaultTargetFps);
          if (!item._lastActiveFps) item._lastActiveFps = displayVal;
      } else {
          displayVal = item.raw_value || String(item.value).replace(/[^0-9]/g, '') || defaultTargetFps;
          item._lastActiveFps = displayVal;
      }
  }
  ```
- **Filtrage des presets :**
  ```javascript
  const filteredOptions = (item.key === 'max_frame_rate')
      ? item.options.filter(opt => String(opt).trim().toUpperCase() !== 'OFF')
      : item.options;
  ```
- **Mise à jour dynamique instantanée (`onMsfsSettingChanged`) :**
  - Actualisation conjointe du switch (`opt-switch-track-*`, `opt-switch-thumb-*`), du badge d'en-tête et des classes de couleur de l'input (`text-emerald-400` vs `text-slate-500 opacity-60`).

---

## 4. Vérification & Validation

1. **Validation syntaxique :**
   - Compilation Python : `python -m py_compile flight_rig_optimizer.py` (Succès, code retour 0).
   - Vérification JavaScript : `node -c web/app.js` (Succès, code retour 0).
2. **Contrôle unitaire de la matrice :**
   - Écran 2D (avec `TargetFrameRate 0` dans `UserCfg.opt`) : `value: 'OFF'`, `raw_value: '0'`, `is_active: False`, `target_fps: 82`, `rating_label: 'OFF'`, `rating_color: 'slate'`, absence totale de `"OFF"` dans `options`.
   - Casque VR (avec `TargetFrameRateVR 45`) : `value: '45 FPS'`, `raw_value: '45'`, `is_active: True`, absence totale de `"OFF"` dans `options`.
