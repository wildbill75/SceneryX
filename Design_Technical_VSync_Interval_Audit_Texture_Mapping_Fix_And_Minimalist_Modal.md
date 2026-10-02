# Design Technique : Audit V-Sync Interval, Correction de Résolution de Texture & Simplification Modale Conflits

## 1. Vue d'Ensemble & Objectifs de la Session

Dans cette itération, trois axes critiques ont été traités sur le moteur de configuration de **SceneryX** pour Microsoft Flight Simulator 2024 :

1. **Refonte Minimaliste de la Modale de Conflit ("Shared Settings Conflicts")** :
   - Élimination intégrale du style visuel surchargé (aucun encadré jaune vif, suppression des bordures d'avertissement et des effets "glass").
   - Suppression totale des emojis et icônes décoratives (🖥️, 🥽, ⚡, ⚠️).
   - Unification de l'argumentaire en un **bloc de texte unique et concis**, débutant impérativement par : *"Scenery X has detected that..."*.
   - Déplacement des explications techniques détaillées dans des infobulles contextuelles natives (`title="..."`) au survol des options.
   - Alignement typographique épuré en nuances ardoise/slate conformément à la charte SceneryX.

2. **Résolution du Bug d'Inversion de Résolution de Texture (`UserCfg.opt`)** :
   - Diagnostic de l'écart constaté (sélection de `Medium` dans l'interface aboutissant à `High` dans MSFS 2024).
   - Correction de l'inversion d'échelle DirectX Mipmap Drop (`Quality 0 = Ultra`, `Quality 1 = High`, `Quality 2 = Medium`, `Quality 3 = Low`).
   - Synchronisation bidirectionnelle de lecture et d'écriture pour éliminer toute incohérence.

3. **Intégration & Audit Exhaustif de la Fonction "V-Sync Interval"** :
   - Ajout du paramètre `vsync_interval` dans la matrice 2D Display (Page 1 : Frame Rate & Sync).
   - Prise en charge des diviseurs harmoniques d'affichage (`100% (1:1)`, `50% (1:2)`, `33% (1:3)`, `25% (1:4)`).
   - Synchronisation automatique avec `TargetFrameRate` et `FrameLimiter`.
   - Audit technique complet sur l'architecture du swap chain DirectX 12, les interactions avec G-Sync/FreeSync, NVIDIA Reflex, DLSS 3 Frame Generation et les casques VR.

---

## 2. Refonte Minimaliste de la Modale Conflits de Paramètres

### 2.1 Principes Directeurs
L'ancienne interface de la modale présentait une surcharge visuelle :
- Deux blocs distincts (`SHARED PIPELINE CONFLICT` avec fond ambré/jaune et `FLIGHT RIG RECOMMENDATION`).
- Des icônes emojis non professionnelles dans les boutons.
- Un sous-titre redondant invitant à choisir.

### 2.2 Nouveau Design Unifié
- **Titre de la fenêtre** : `Shared Settings Conflicts`
- **Texte unique** :
  > *"Scenery X has detected that both your 2D Display (82 FPS) and VR Headset (45 FPS) Max Frame Rates are active. MSFS 2024 uses a single global FrameLimiter in its rendering pipeline and cannot enforce two different caps simultaneously. We recommend maintaining dedicated profiles (e.g. "2D Desktop" and "VR Headset") rather than a shared configuration."*
- **Boutons épurés avec infobulles contextuelles** :
  - `Enforce 2D Target (82 FPS)` : `title="Sets engine FrameLimiter to the 2D sync target and turns OFF the VR limiter for this profile."`
  - `Enforce VR Target (45 FPS)` : `title="Sets engine FrameLimiter to the VR sync target and turns OFF the 2D limiter for this profile."`
  - `Run Uncapped (OFF)` : `title="Disables MSFS internal limiter; ideal if pacing is governed by RivaTuner or NVIDIA Control Panel."`

---

## 3. Bug de Résolution de Texture : Analyse & Correction

### 3.1 Anatomie du Bug
Dans la majorité des sous-blocs de `UserCfg.opt` (`{VolumetricClouds`, `{ContactShadows`, `{Buildings`, `{OffscreenTerrainPreCaching`), la progression de la qualité suit l'ordre arithmétique standard :
- `0 = Low`, `1 = Medium`, `2 = High`, `3 = Ultra`.

Cependant, dans la section `{Texture`, Microsoft Flight Simulator utilise la convention bas niveau des moteurs 3D basée sur le **Mipmap Drop Level** (nombre de niveaux de mipmap ignorés lors du streaming mémoire) :
- `Quality 0` : 0 mipmaps sautés = **Ultra** (résolution 4K native intégrale).
- `Quality 1` : 1 mipmap sauté = **High** (résolution divisée par 2 / 2K).
- `Quality 2` : 2 mipmaps sautés = **Medium** (résolution divisée par 4 / 1K).
- `Quality 3` : 3 mipmaps sautés = **Low** (résolution divisée par 8 / 512px).

L'ancien code appliquait l'échelle classique `0=Low, 1=Medium, 2=High, 3=Ultra`. Par conséquent :
- Lorsque l'utilisateur demandait `Medium`, SceneryX écrivait `Quality 1`.
- MSFS lisait `Quality 1` et activait **HIGH** !
- Réciproquement, un réglage `Low` écrivait `Quality 0` (activant Ultra dans le jeu).

### 3.2 Correction Appliquée
Dans `flight_rig_optimizer.py` :
1. **Écriture (`update_msfs_user_cfg_setting`)** :
   ```python
   # 11. Texture Resolution (MSFS uses inverted mipmap drop level: 0=Ultra, 1=High, 2=Medium, 3=Low)
   elif setting_key in ['texture_resolution', 'Texture']:
       v_clean = str(new_value).lower().strip()
       if 'ultra' in v_clean or v_clean == '0':
           clean_q = '0'
       elif 'high' in v_clean or v_clean == '1':
           clean_q = '1'
       elif 'medium' in v_clean or 'med' in v_clean or v_clean == '2':
           clean_q = '2'
       elif 'low' in v_clean or v_clean == '3':
           clean_q = '3'
       else:
           clean_q = '2'
       content = update_sub_block_setting(content, mode, '{Texture', r'(Quality\s+)[^\r\n]+', rf'\g<1>{clean_q}', f"Quality {clean_q}")
   ```
2. **Lecture (`extract_msfs_settings_matrix`)** :
   ```python
   # 9. Texture Quality (MSFS inverted mip-drop scale: 0=Ultra, 1=High, 2=Medium, 3=Low)
   tex_q_map = {'0': 'Ultra', '1': 'High', '2': 'Medium', '3': 'Low'}
   tex_2d_raw = get_block_val(r'Quality\s+(\d+)', extract_block(g2d, '{Texture'), '1')
   tex_2d_val = tex_q_map.get(tex_2d_raw, 'High')
   tex_vr_raw = get_block_val(r'Quality\s+(\d+)', extract_block(gvr, '{Texture'), '2')
   tex_vr_val = tex_q_map.get(tex_vr_raw, 'Medium')
   ```
3. **Mise à jour immédiate du fichier `UserCfg.opt`** :
   - Les sections 2D et VR ont été synchronisées sur `Quality 2`, confirmant l'affichage `Medium` dans MSFS.

---

## 4. Audit Technique Complet : V-Sync Interval dans MSFS 2024

### 4.1 Rôle & Fonctionnement Bas Niveau (DirectX 12 Swap Chain)
Dans Microsoft Flight Simulator 2024, le paramètre `V-Sync Interval` régit directement l'appel de présentation de l'API graphique bas niveau :
$$\text{IDXGISwapChain::Present(SyncInterval, Flags)}$$

En mode Borderless Fullscreen sous Windows 11 avec le Flip Model DX12 (`DXGI_SWAP_EFFECT_FLIP_DISCARD`), l'argument `SyncInterval` dicte le comportement de la file d'attente de balayage vertical (Vertical Blanking Interval / V-Blank) :
- **`SyncInterval = 0` (V-Sync OFF)** : La mémoire tampon arrière (*back buffer*) est présentée au Desktop Window Manager (DWM) dès son achèvement, sans attendre le balayage de l'écran. Cela génère des coupures horizontales (*tearing*) dès que la cadence du moteur ne correspond pas exactement au rafraîchissement physique de la dalle.
- **`SyncInterval = 1` (100% Refresh Rate / 1:1)** : La présentation est synchronisée avec chaque impulsion V-Blank. Sur un écran 165 Hz, le jeu tente d'afficher 165 FPS. Si le processeur (MainThread) faiblit ne serait-ce que d'une microseconde, la trame est retardée d'un cycle complet, provoquant un micro-bégaiement (*stutter*).
- **`SyncInterval = 2` (50% Refresh Rate / 1:2)** : La présentation est verrouillée sur une impulsion V-Blank sur deux. Sur un écran 165 Hz, le débit est exactement calibré à **82.5 -> 82 FPS** (ou 60 FPS sur 120 Hz, 72 FPS sur 144 Hz). C'est le ratio d'or pour la simulation de vol.
- **`SyncInterval = 3` (33% Refresh Rate / 1:3)** : La présentation s'effectue toutes les 3 impulsions (55 FPS sur 165 Hz, 48 FPS sur 144 Hz, 40 FPS sur 120 Hz). Idéal pour les gros porteurs complexes (Fenix A320, PMDG 777) sur les aéroports les plus denses.
- **`SyncInterval = 4` (25% Refresh Rate / 1:4)** : Présentation toutes les 4 impulsions (41 FPS sur 165 Hz, 36 FPS sur 144 Hz, 30 FPS sur 120 Hz).

### 4.2 La Dualité avec `TargetFrameRate` & `FrameLimiter`
Dans le fichier `UserCfg.opt`, le moteur MSFS maintient une corrélation étroite entre le diviseur de synchronisation et la régulation CPU :
1. `VSync 1` active la barrière de synchronisation swap chain.
2. `VSyncInterval N` spécifie le diviseur DirectX 12.
3. `TargetFrameRate` et `FrameLimiter` définissent la temporisation de la boucle interne du moteur (`Tick()`).

Si `VSync` est configuré sur un diviseur 1:2 (ex: 82 FPS sur un écran 165 Hz) mais que `FrameLimiter` est positionné sur une valeur non harmonique (ex: 65 FPS), les deux mécanismes entrent en interférence destructive :
- La boucle de jeu calcule les trames à 65 FPS.
- Le swap chain n'accepte de présenter qu'à 82.5 FPS ou 55 FPS.
- Résultat : une gigue temporelle constante (*pacing jitter*) où des images sont dupliquées de façon asymétrique (schéma 1-2-1-2-2-1), détruisant la fluidité perçue.

**Bénéfice SceneryX** : SceneryX assure l'alignement mathématique absolu :
$$\text{TargetFrameRate} = \text{FrameLimiter} = \left\lfloor \frac{\text{Screen\_Hz}}{N} \right\rfloor$$

### 4.3 Interaction avec NVIDIA Reflex Low Latency
NVIDIA Reflex modifie le comportement traditionnel du V-Sync :
- En V-Sync classique, un buffer plein génère une file d'attente d'attente de 2 à 3 trames côté GPU, introduisant une latence de commande (*input lag*) sensible lors des arrondis à l'atterrissage.
- Lorsque **Reflex est positionné sur ON**, le pilote NVIDIA injecte des marqueurs de synchronisation semi-asynchrones qui vident la file d'attente juste avant que le CPU ne commence la frame suivante.
- L'association **`VSync ON` + `V-Sync Interval 50%` + `Reflex ON`** garantit ainsi l'absence absolue de tearing tout en éliminant la pénalité de latence classique du V-Sync.

### 4.4 Interaction avec DLSS 3 Frame Generation
Dans l'interface de MSFS 2024, lorsque **Frame Generation (DLSSG)** est activé, l'option V-Sync est fréquemment grisée :
- La génération d'images par flux optique (Optical Flow Accelerator) insère des images calculées par IA directement entre les frames natives rendues par le moteur.
- Lorsque Frame Gen est actif, la fréquence perçue est doublée ($2 \times \text{FPS Moteur}$).
- Si l'utilisateur vise 82 FPS affichés sur son écran 165 Hz avec Frame Gen, le moteur interne n'a besoin de calculer que **41 FPS** !
- SceneryX configure les paramètres directement au niveau de `UserCfg.opt`, garantissant que le Frame Generation fonctionne en harmonie avec le limiteur sans provoquer de saccades de pacing.

### 4.5 Casques VR vs Écran 2D
Le paramètre `V-Sync Interval` est strictement réservé au mode **2D Display** :
- Les casques VR (OpenXR, SteamVR, Pimax Play, Meta Quest Link) contournent intégralement le swap chain DXGI du bureau Windows.
- La cadence VR est gérée exclusivement par le compositeur OpenXR au moyen de l'Asynchronous TimeWarp (ATW) ou de la Motion Reprojection (diviseurs VR 1/2 ou 1/3, ex: 45 FPS pour un casque 90 Hz, 36 FPS pour 72 Hz).
- C'est pourquoi SceneryX isole judicieusement `V-Sync Interval` dans la rubrique 2D Frame Rate & Sync, évitant toute pollution dans les réglages VR.

---

## 5. Synthèse des Modifications Techniques Réalisées

| Fichier | Nature de la Modification | Impact Fonctionnel |
| :--- | :--- | :--- |
| [`web/index.html`](file:///D:/SceneryX/web/index.html) | Simplification de la modale `opt-framelimiter-conflict-modal` | Suppression des encadrés jaunes, bordures glass et icônes ; titre unifié `Shared Settings Conflicts` ; infobulles natives. |
| [`web/app.js`](file:///D:/SceneryX/web/app.js) | Adaptation de `openFrameLimiterConflictModal` | Injection du texte unique concis débutant par *"Scenery X has detected that..."*. |
| [`flight_rig_optimizer.py`](file:///D:/SceneryX/flight_rig_optimizer.py) | Correction `clean_q` Texture dans `update_msfs_user_cfg_setting` | Mipmap drop inversé (0=Ultra, 1=High, 2=Medium, 3=Low) : écrire Medium écrit désormais `Quality 2`. |
| [`flight_rig_optimizer.py`](file:///D:/SceneryX/flight_rig_optimizer.py) | Correction `tex_q_map` dans `extract_msfs_settings_matrix` | Lecture fidèle de `Quality 2` en `Medium` et `Quality 1` en `High`. |
| [`flight_rig_optimizer.py`](file:///D:/SceneryX/flight_rig_optimizer.py) | Ajout de la gestion `vsync_interval` | Lecture, écriture et synchronisation dynamique des diviseurs de rafraîchissement avec `TargetFrameRate`. |
| [`flight_rig_optimizer.py`](file:///D:/SceneryX/flight_rig_optimizer.py) | Enrichissement `SETTING_DESCRIPTIONS` & `option_ratings` | Documentation intégrée et scores d'impact matériel pour `V-Sync Interval`. |
| [`UserCfg.opt`](file:///C:/Users/Bertrand/AppData/Local/Packages/Microsoft.Limitless_8wekyb3d8bbwe/LocalCache/UserCfg.opt) | Mise à jour de la configuration réelle | `{Texture Quality 2}` appliquée pour 2D et VR (Medium effectif). |
| [`SceneryX.exe`](file:///D:/SceneryX/SceneryX.exe) | Régénération exécutable autonome | Intégration de toutes les corrections dans le binaire standalone. |
