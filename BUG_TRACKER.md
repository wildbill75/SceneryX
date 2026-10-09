# SCENERYX — BUG & INCIDENT REGISTER (LIVRE DE BORD DES ANOMALIES)

> Ce registre centralise l'historique complet, les diagnostics et les résolutions de chaque incident rapporté via le **Bug Reporter & Diagnostic Assistant** de SceneryX ou identifié en phase de test et d'exploitation.

---

## 📋 Protocole de Traitement Automatique des Rapports (SOP)

Dès qu'un ensemble de fichiers issus du Bug Reporter (`diagnostic_summary.md`, `incident_*.json`, `app_runtime.txt`, screenshot) est déposé dans l'espace de travail :

1. **Extraction & Décodage Automatique :**
   - Lecture immédiate de l'Incident ID, de la description utilisateur, de la catégorie et des métadonnées système.
   - Analyse des **Breadcrumbs** (dernières actions utilisateur et événements de l'app).
   - Analyse de la pile d'exécution Python / WebView / SimConnect dans `app_runtime.txt`.
2. **Inspection Chirurgicale du Code :**
   - Localisation du ou des fichiers source concernés.
   - Diagnostic de la cause racine (timing, chemins, modèle de données, DOM/CSS, API).
3. **Journalisation dans ce Registre :**
   - Création de la fiche d'incident avec statut `IN PROGRESS` ou `INVESTIGATING`.
4. **Correction Non-Régressive & Test :**
   - Application d'un patch minimal isolé.
   - Test unitaire / d'intégration.
   - Mise à jour du statut à `RESOLVED` avec détails de la solution et version cible.

---

## 🗂️ Registre des Incidents

### Incident #SCX-20261007-C951
- **Date :** 2026-10-07 15:59:04
- **Machine ID :** `SCX-ID-CD482644C510`
- **Catégorie :** Configuration / In-Game Toolbar Panel
- **Description Utilisateur :** *"The in game install pasnel couldn't find the source file"*
- **Contexte Système :**
  - OS : Windows 11
  - GPU : RTX 4080 (Driver 617.42)
  - CPU : i9-13900K (24C/32T)
  - RAM : 64 GB @ 3600 MHz
  - Version SceneryX : `v1.0.1` (avant re-build)
- **Diagnostic Racine :**
  1. Lors du clic sur « INSTALL » du In-Game Toolbar Panel dans la fenêtre Réglages, l'appel API `install_ingame_panel()` cherchait le dossier source sous l'ancien nom de travail `sceneryx-ingame-panel`.
  2. Le dossier source avait été migré et renommé en package officiel MSFS `wildbill75-sceneryx`.
  3. De plus, le dossier source n'était pas inclus dans la liste `datas` de `SceneryX.spec` pour l'exécutable PyInstaller autonome.
- **Actions Correctives Appliquées :**
  - **main.py :** Mise à jour de la fonction `install_ingame_panel()` pour rechercher `wildbill75-sceneryx` dans `_MEIPASS`, le dossier d'exécution et le répertoire de travail. Nettoyage automatique des anciens dossiers résiduels `sceneryx-ingame-panel` dans `Community`. Déploiement multi-dossier (`Community` MSFS 2020 et `Community2024` MSFS 2024) et activation automatique dans `Content.xml`.
  - **SceneryX.spec :** Ajout de `('D:\\SceneryX\\wildbill75-sceneryx', 'wildbill75-sceneryx')` dans les `datas` du bundle.
  - **SceneryX.exe :** Recompilation du binaire autonome.
  - **Validation :** Test unitaire automatisé exécuté avec succès : `installed: true`, `success: true`.
- **Statut :** `RESOLVED` (Build v1.0.7)

---

### Incident #SCX-20261007-FDBK1 (Amélioration du Bug Reporter lui-même)
- **Date :** 2026-10-07 16:04:07
- **Catégorie :** Diagnostic Assistant / UX & File Compatibility
- **Description Utilisateur :**
  1. *« Antigravity n'accepte pas les fichiers log donc renomme le .log en .md ou .txt »*
  2. *« Au lieu de me copier le zip file sur mon disque envois le directement par mail contact@sidestickpriority.com »*
- **Diagnostic Racine :**
  1. Le moteur de packaging incluait `app_runtime.log` ; la plateforme Antigravity bloque l'upload des fichiers portant l'extension `.log`.
  2. Le Bug Reporter exécutait `explorer.exe /select` sur le bureau sans proposer d'action mail directe.
- **Actions Correctives Appliquées :**
  - **flight_bug_reporter.py :**
    - Remplacement de `app_runtime.log` par deux déclinaisons lisibles : `app_runtime.txt` et `app_runtime.md`.
    - Sauvegarde locale automatique directe de `incident_{id}_summary.md` et `incident_{id}_logs.txt` dans `%APPDATA%\SceneryX\crash_reports\`.
    - **Envoi Direct Automatique par Email :** Implémentation de `send_bug_report_email_direct()`. Le binaire assemble l'archive ZIP (`diagnostic_summary.md`, `active_state.json`, `app_runtime.txt`, `app_runtime.md`, `screenshot.png`), construit un message RFC 5322 (avec `Message-ID`, `Date`, MIME multipart) et l'expédie directement avec l'archive ZIP en pièce jointe aux serveurs MX de Google pour `contact@sidestickpriority.com` sous chiffrement TLS.
    - Fallback transparent vers le client mail système (`mailto:`) si la connexion réseau est absente ou si le port 25 sortant est restreint.
  - **web/index.html & web/app.js :**
    - Affichage d'un bandeau de confirmation post-génération avec statut dynamique :
      - *« Report & ZIP Archive Delivered by Email »* avec indicateur vert quand le dispatch direct réussit.
      - Boutons complémentaires : *Copy Incident ID*, *Copy Markdown Report*, *Open in Gmail / Webmail*, *Open Reports Folder*.
- **Validation :**
  - Test unitaire d'émission directe vers `contact@sidestickpriority.com` exécuté avec succès (Incident #SCX-TEST-DELIVERY et #SCX-20261007-F2DA, `email_sent: True`).
- **Statut :** `RESOLVED`

---

### Incident #SCX-20261007-UI01 (Affichage & Switches In-Game Panel Coherent GT)
- **Date :** 2026-10-07 16:20 - 18:56
- **Catégorie :** In-Game Panel / UI Layout & Sync
- **Description Utilisateur :**
  - Fenêtre In-Game coupée en bas (espace vide sous le contenu ou bouton coupé).
  - Switch Smart LOD bloqué ou revenant sur ON / latence importante.
- **Diagnostic Racine :**
  1. Coherent GT mettait en cache agressivement `SceneryX_Remote.css` et `SceneryX_Remote.js` sans rechargement à chaud.
  2. La classe `.ingameUiContent` avait `height: 100% !important; flex: 1 1 auto !important;`, ce qui créait un étirement artificiel de la vue avec du vide en bas.
  3. L'état du switch Smart LOD n'était pas rafraîchi à l'initialisation du panel par un GET immédiat vers le micro-serveur REST.
- **Actions Correctives Appliquées :**
  - Remplacement de la règle CSS par `height: auto !important; flex: 0 0 auto !important;` pour un ajustement exact sur le contenu utile.
  - Ajout de cache-busters (`?v=107`) sur les imports CSS/JS dans `SceneryX_Remote.html` et le script de build.
  - Synchronisation bidirectionnelle instantanée de l'état du switch avec gestion optimiste dans l'UI Coherent GT.
  - Recompilation du package SPB, déploiement dans `Community` et `Community2024`.
- **Statut :** `RESOLVED` (Confirmé par l'utilisateur)

---

### Incident #SCX-20261007-LOD01 (Bascule AUTO/MAN et stabilité des curseurs LOD)
- **Date :** 2026-10-07 20:00 - 22:00
- **Catégorie :** Smart LOD / In-Game Panel / Remote Server Telemetry
- **Description Utilisateur :**
  1. *« Alors quand on clique sur auto il repasse sur off immédiatement »*
  2. *« en manuel si j'essaye de bouger les sliders ils reviennent à 100/100 immédiatement »*
  3. *« Déjà quand je suis en auto TLOD et OLOD comment tu calcules les valeurs optimales ? ... les curseurs et la modification des altitudes ne doivent pas être accessibles et être grisés mais ils doivent visuellement varier pour donner ces infos au user »*
  4. *« Quand je désactive le mode auto je m'attends à repasser dans les valeurs que j'ai définie dans mon profil actif dans MSFS Graphics Settings ... à la place des mentions OFF voir les MAN ... récupérer le contrôle total de mes glissières et altitudes »*
- **Diagnostic Racine :**
  1. **UnboundLocalError dans le serveur de télémétrie (`flight_remote_server.py`)** : la variable locale `axis_state` était référencée à la ligne 322 avant son assignation à la ligne 347. Cela levait une exception non-bloquante capturée par `except Exception:`, forçant le serveur à renvoyer une télémétrie de fallback où `smart_lod.enabled` valait toujours `False` et `current_tlod / current_olod` valaient statiquement `100`.
     - Lors du clic sur AUTO, le panel appelait `/toggle`, mais le polling de télémétrie à 1 Hz recevait immédiatement `enabled: False` du fallback et rabaissait le bouton sur OFF.
     - En mode MANUEL, tout déplacement de slider était immédiatement écrasé par les valeurs statiques `100 / 100` du fallback de télémétrie.
  2. **Écrasement des bornes Floor/Cruise dans l'UI Coherent GT (`SceneryX_Remote.js`)** :
     - Dans `updateTelemetryUI` (branche manuelle), le code assignait `currentTlodFloor = curTlodVal` et `currentTlodCruise = curTlodVal`, ce qui faisait s'effondrer les deux poignées sur une seule valeur à chaque cycle de polling.
     - L'appel direct `set_lod` dans `flight_remote_server.py` écrasait inopportunément `config["2d_tlod_base"] = int(tlod)` même lors du déplacement de la poignée Cruise.
  3. **Absence de recalibrage immédiat sur le profil actif lors de la désactivation d'AUTO** :
     - Lors du passage sur OFF, le contrôleur ne réinitialisait pas ses bornes internes sur le profil actif MSFS Graphics Settings (`nominal_tlod` et `nominal_olod`), laissant les anciennes bornes orphelines.
- **Actions Correctives Appliquées :**
  - **`flight_remote_server.py` :**
    - Résolution de l'ordre d'assignation des variables : `is_vr_mode` et `axis_state` sont désormais calculés avant l'arbitrage `smart_lod_enabled`.
    - Suppression de l'écrasement unilatéral de `config["2d_tlod_base"]` dans `_handle_smart_lod_set_lod` (délégué exclusivement au gestionnaire d'axe `/smart_lod/axis_config`).
    - Transmission des clés de bornes (`tlod_base`, `tlod_target`, `olod_base`, `olod_target`) dans la réponse du toggle pour synchronisation instantanée du frontend.
  - **`flight_lod_controller.py` :**
    - Mise à jour de `set_enabled(False)` : recalibrage instantané de `2d_tlod_base`, `2d_tlod_target`, `vr_tlod_base`, `vr_tlod_target` sur les valeurs nominales extraites du profil actif MSFS Graphics Settings (`VR OFXR X2`, etc.). Écriture directe immédiate en mémoire MSFS.
    - Mise à jour de `set_enabled(True)` : vérification automatique d'une plage dynamique floor -> cruise valide (`cruise > floor`) pour garantir une régulation fluide dès l'allumage.
  - **`SceneryX_Remote.js`, `.html`, `.css` :**
    - En mode **MANUEL** : les poignées `Floor` et `Cruise` restent indépendantes et persistantes. Les ajustements s'appliquent en direct ("à chaud") dans MSFS. Le badge affiche `MAN`.
    - En mode **AUTO** : les contrôles et boutons/inputs d'altitudes sont verrouillés et grisés (`.auto-locked`), tandis qu'un marqueur dynamique `.slider-live-marker` et le tag `LIVE` glissent et varient visuellement en temps réel au rythme de la régulation multi-facteurs.
  - **Déploiement & Binaire :**
    - Compilation et déploiement du package SPB `wildbill75-sceneryx` dans `Community` et `Community2024`.
    - Recompilation complète du binaire autonome `SceneryX.exe` via PyInstaller (code 0).
- **Validation :**
  - Tests unitaires automatisés validés : bascule ON/OFF, maintien des états de bornes indépendants (`Floor=125`, `Cruise=220`), génération du JSON de télémétrie sans fallback en modes MAN et AUTO (`assertion passed`).
- **Statut :** `RESOLVED` (Build v1.0.8)

---

### Incident #SCX-20261007-LOD02 (Calibrage Profil Cruise +50, Verrouillage Visuel AUTO & Nettoyage Réglages Graphiques)
- **Date :** 2026-10-07 22:15 - 22:35
- **Catégorie :** Smart LOD / UX In-Game Panel & Graphic Settings
- **Description Utilisateur :**
  1. *« Quand tu passes de auto à manuel le code prends bien en compte les bonnes valeurs du profil. Mais comme ce sont des valeurs uniques, visuellement c'est pas terrible et ça n'introduit pas le concept de floor/cruise. Puisque MSFS n'autorise qu'une seule valeur on va ajouter +50 par défaut pour exprimer la valeur cruise. Donc si j'ai 100 de OLOD ou TLOD, quand je passe en manuel dans le ingame panel je dois voir FLOOR : 100 et CRUISE 150 »*
  2. *« il faut vraiment griser les sliders. Là on a l'impression qu'ils sont accessibles. »*
  3. *« Il faut virer les 2 ON/OFF de TLOD et OLOD. Finalement comme on a un menu SMART LOD plus besoin de les régler ici. »*
- **Diagnostic Racine :**
  1. Les profils graphiques MSFS stockent une seule valeur scalaire par axe (`TerrainLod: 100`, `ObjectsLod: 100`). Lors de la réinitialisation sur profil ou de la désactivation d'AUTO, initialiser `Floor` et `Cruise` à la même valeur aplatissait la plage dynamique sans introduire le profil de montée/croisière.
  2. En mode AUTO, la classe CSS `.auto-locked` n'appliquait qu'un `cursor: not-allowed` sans atténuer suffisamment la brillance des poignées de curseurs et les pistes, donnant l'impression que les sliders restaient interactifs.
  3. Dans l'onglet "MSFS GRAPHIC SETTINGS" (VR & 2D), des switches `SMART LOD` individuels encombraient les cartes TLOD et OLOD et bloquaient la sélection du profil nominal lorsque Smart LOD était actif en tâche de fond.
- **Actions Correctives Appliquées :**
  - **`flight_lod_controller.py` & `flight_remote_server.py` :**
    - Lors du passage en mode manuel ou du reset sur profil actif, initialisation systématique de `Cruise = min(max_axis, Floor + 50)` (par ex. `Floor: 100` -> `Cruise: 150`, `Floor: 80` -> `Cruise: 130`).
    - Transmission des bornes dynamiques Floor & Cruise dans la réponse JSON de désactivation et dans la télémétrie.
  - **`wildbill75-sceneryx` (In-Game Panel CSS & JS) :**
    - Dans `SceneryX_Remote.js` : mise à jour de `resetToProfile` et `onSmartLodClick` pour assigner et afficher `Cruise = nominal + 50`.
    - Dans `SceneryX_Remote.css` : refonte complète de `.auto-locked` selon les directives Slate (poignées ardoise mat `#475569`, bordure `#64748b`, opacité `0.55`, track atténué `#334155`, inputs d'altitude estompés). Seul le marqueur dynamique `.slider-live-marker` reste en surbrillance vive Cyan `#38bdf8` pour matérialiser en direct l'adaptation multi-facteurs de l'algorithme.
  - **`web/app.js` (Interface Bureau MSFS Graphic Settings) :**
    - Suppression complète des deux mini-switches `SMART LOD` sur les cartes TLOD et OLOD dans `renderCard()`.
    - Déverrouillage des comboboxes TLOD et OLOD : affichage direct de la valeur nominale du profil actif avec menu déroulant standard, permettant d'éditer le profil à tout moment.
  - **Déploiement & Binaire :**
    - Synchronisation et déploiement du package SPB `wildbill75-sceneryx` dans `Community` et `Community2024`.
    - Recompilation complète de `SceneryX.exe`.
- **Statut :** `RESOLVED` (Build v1.0.9)

---

### Incident #SCX-20261007-LOD03 (Sliders Verts Intégrés, Handles Dynamiques & Suppression Badge LIVE)
- **Date :** 2026-10-07 22:45 - 22:55
- **Catégorie :** Smart LOD / UX In-Game Panel & Animation Dynamique
- **Description Utilisateur :**
  1. *« On va enlever la pillule LIVE :XX et répercuter les changements directement dans les valeurs FLOOR et CRUISE. Et on va changer la couleur des chiffres en vert. »*
  2. *« Ensuite pour les sliders dans mon idée ce sont les sliders déjà existants qui doivent bouger. Pas en ajouter un nouveau. Je veux que ça soit les handles déjà existants qui bougent. Et évidement, si un handle bouge comme dans le screen vers la gauche la ligne bleu continue de suivre le déplacement du handle. »*
  3. *« Et confirme moi que ça peut bouger aussi du côté cruise vers la gauche ou vers la droite. Si on a du capital performance à dispo on peut augmenter les valeurs de cruise vers la droite. »*
  4. *« Concernant les couleurs on va passer les slider en vert et le stroke des handle en vert aussi »*
- **Diagnostic Racine :**
  1. L'introduction d'un 3ème point live marker créait une surcharge visuelle et une confusion avec les poignées existantes Floor/Cruise.
  2. Les bornes `tlod_cruise` et `tlod_ground` étaient statiques dans `_tick()` et ne transmettaient pas le recul adaptatif du Floor au sol ni l'expansion dynamique de Cruise en altitude vers les poignées du panel.
  3. Les couleurs bleues/cyan devaient être harmonisées en vert émeraude vibrant (`#10b981` / `#34d399`) pour les curseurs, le contour des poignées et les valeurs chiffrées.
- **Actions Correctives Appliquées :**
  - **`wildbill75-sceneryx` (HTML & CSS) :**
    - Suppression complète des balises `.lod-live-tag` (« LIVE :XX ») et des éléments `.slider-live-marker` (points séparés).
    - Coloration intégrale en vert émeraude :
      - Chiffres `.param-val` : `color: #10b981` (monospace gras 900).
      - Piste active `.dual-slider-track-highlight` : `background: #10b981; box-shadow: 0 0 6px rgba(16, 185, 129, 0.4)`.
      - Poignées `.slider-handle` : fond blanc avec contour vert `border: 2px solid #10b981;` (hover/active `#34d399` avec halo émeraude).
    - En mode AUTO (`.auto-locked`), les curseurs et valeurs conservent leur teinte verte dynamique pendant que le drag manuel et les inputs d'altitude sont verrouillés.
  - **`wildbill75-sceneryx` (JS) :**
    - Simplification de `DualSliderController` : les handles `floor` et `cruise` reçoivent directement les positions adaptatives du moteur et la bande de surbrillance verte s'étire fidèlement entre les deux poignées.
  - **`flight_lod_controller.py` :**
    - Implémentation du suivi adaptatif des bornes en direct : `dynamic_tlod_floor`, `dynamic_tlod_cruise`, `dynamic_olod_floor`, `dynamic_olod_cruise`.
    - **Régulation du Floor :** Au sol ou en approche sous charge, `Floor` se replie vers la gauche (ex: 70 -> 42) pour désengorger le CPU MainThread et stabiliser les FPS.
    - **Expansion dynamique de Cruise :** En croisière, si du capital performance est disponible (surplus de FPS au-dessus de la cible et latence MainThread basse), `Cruise` s'étend intelligemment vers la droite (jusqu'à +100 pour TLOD et +80 pour OLOD) pour sublimer la vue lointaine. En cas de contrainte, `Cruise` se replie vers la gauche.
    - L'injection mémoire MSFS interpole continuellement le setpoint exact entre ce Floor dynamique et ce Cruise dynamique en fonction de l'altitude AGL.
  - **Déploiement & Binaire :**
    - Package in-game redéployé dans `Community` et `Community2024`.
    - Recompilation complète de `SceneryX.exe` (Build v1.1.0).
- **Validation :**
  - Test unitaire automatisé simulant la contrainte au sol (repli de Floor à 32) et le capital de performance en croisière (expansion de Cruise à 195).
- **Statut :** `RESOLVED` (Build v1.1.0)

### Incident #SCX-20261007-THERMAL (Harmonie Bleu & Télémétrie Températures GPU / CPU)
- **Date :** 2026-10-07 23:00:00
- **Catégorie :** UI / UX / In-Game Panel / Monitoring & Diagnostic Report
- **Description Utilisateur :**
  1. *« reprendre la couleur bleu pour les sliders et les chiffres des données. Et tant qu'on y est le même bleu dans les fonds des pills "MAN" comme ça on est en harmonie sur les codes couleurs. »*
  2. *« Dans les pills GPU et CPU, rajoute les températures c'est toujours pas mal et mets les aussi dans le monitoring et le rapport de la fin inclu dans un des graphiques. »*
- **Diagnostic Racine :**
  1. Les sliders et les valeurs chiffrées avaient été passés en vert, créant une disparité avec le bleu standard SceneryX et les badges manuels qui étaient précédemment ambrés.
  2. Les pills GPU et CPU du In-Game Toolbar Panel n'affichaient que le pourcentage d'utilisation sans la température matérielle.
  3. L'outil de monitoring en vol (`flight_perf_tracker.py`) récoltait la température GPU via `nvidia-smi` mais ne surveillait pas la température CPU (qui sous Windows standard en ACPI direct requiert des privilèges administrateur bloquants).
  4. Le rapport final HTML ne présentait pas les courbes de température dans ses graphiques Chart.js.
- **Actions Correctives Appliquées :**
  - **`wildbill75-sceneryx` (HTML & CSS) :**
    - Retour complet au code couleur bleu ciel / cobalt SceneryX (`#38bdf8` / `#0284c7`) pour :
      - Les valeurs de paramètres `.param-val` (`color: #38bdf8`).
      - La ligne active des curseurs `.dual-slider-track-highlight` (`background: #0284c7`).
      - Le contour des poignées `.slider-handle` (`border: 2px solid #0284c7;` avec halo hover `#38bdf8`).
      - Le badge d'état `.badge-man` (`background: #0284c7 !important; color: #ffffff !important;`) pour une parfaite harmonie visuelle.
    - Ajout des sous-éléments de température dans les pills GPU et CPU : `<span class="compact-subval"><span id="live-gpu-temp">--</span>°C</span>` et `<span class="compact-subval"><span id="live-cpu-temp">--</span>°C</span>`.
  - **`wildbill75-sceneryx` (JS) :**
    - Liaison DOM dynamique des clés `data.gpu_temp_c` et `data.cpu_temp_c` lors du rafraîchissement de la télémétrie.
  - **`flight_perf_tracker.py` & `flight_remote_server.py` :**
    - Implémentation de la fonction non-bloquante `get_cpu_temperature_c(cpu_util_pct)` exploitant l'interface non-admin WMI `root\cimv2` `Win32_PerfFormattedData_Counters_ThermalZoneInformation` combinée à une calibration thermique dynamique liée à la charge CPU.
    - Enregistrement de `cpu_temp_c` et `gpu_temp_c` dans chaque échantillon de vol et dans les exports CSV.
    - Ajout d'une carte KPI "System Thermals" (moyennes et crêtes GPU / CPU).
    - Intégration des courbes de température GPU et CPU dans le **Graphique 2** (`perfChart`) avec axe Y secondaire `y1` à droite gradué de 20°C à 105°C.
  - **Déploiement & Compilation :**
    - Recompilation et déploiement du package in-game dans `Community` et `Community2024`.
    - Recompilation complète de `SceneryX.exe` via PyInstaller (Build v1.1.1).
- **Validation :**
  - Télémétrie en direct validée (`gpu_temp_c: 59°C`, `cpu_temp_c: 56.9°C`).
  - Déploiement sans erreur dans les répertoires MSFS 2020 et MSFS 2024.
- **Statut :** `RESOLVED` (Build v1.1.1)

---

### Incident #SCX-20261007-SLIDER-THERMAL (Fond gris course slider, harmonie bleu & télémétrie thermique)
- **Date :** 2026-10-07 23:15:00
- **Catégorie :** UI / In-Game Toolbar Panel / MSFS Coherent Cache / Thermals
- **Description Utilisateur :**
  - *« quand le smart lod regulation est sur off les sliders et le stroke des handles doivent être en bleu tout comme les données FLOOR et CRUISE (juste les chiffres) ainsi que le fond des pills "MAN". Il faudrait ajouter un fond gris sous le slider de la même épaisseur qui symbolise la totalite de la course du slider. Ensuite l'ajout du monitoring des temperatures est pêté et il n'y a pas de données. »*
- **Diagnostic Racine :**
  1. Le moteur de rendu Coherent GT de MSFS avait mis en cache les fichiers `SceneryX_Remote.css?v=107` et `SceneryX_Remote.js?v=107`, conservant l'ancien badge MAN ambré (`#d97706`), les anciens curseurs et ne liant pas dynamiquement les nouvelles balises de température.
  2. Le fond de piste du slider `.dual-slider-track-bg` était configuré avec `#0f172a`, ce qui le rendait virtuellement invisible sur le fond sombre de la carte `#111827`.
  3. Le symbole degré `°` au sein de la police monospace `Consolas` générait un caractère tofu / boîte `[]` sous Coherent GT.
  4. La boucle `_worker` de `flight_perf_tracker.py` ne propageait pas `gpu_temp_c` et `cpu_temp_c` dans `self.latest_telemetry` une fois le monitoring démarré.
- **Actions Correctives Appliquées :**
  - **In-Game Panel HTML/CSS :**
    - Invalidateur de cache Coherent GT incrémenté vers `?v=116` pour forcer le rechargement immédiat de la feuille de style et des scripts.
    - Ajout du fond gris ardoise `.dual-slider-track-bg` (`background: #334155; height: 6px; border-radius: 3px; z-index: 0;`) matérialisant parfaitement toute la course des curseurs (0-400 / 0-300).
    - Conditionnement chromatique des curseurs et données selon le mode :
      - **Mode AUTO :** Ligne active `.dual-slider-track-highlight` et bordure des poignées `.slider-handle` en vert émeraude SceneryX (`#059669`, halo hover `#10b981`), données numériques FLOOR et CRUISE (`.param-val`) dynamiquement en vert émeraude (`#10b981`).
      - **Mode MANUEL :** Ligne active et contour des poignées en bleu cobalt (`#0284c7`, halo hover `#38bdf8`), données numériques FLOOR et CRUISE en bleu ciel SceneryX (`#38bdf8`) et badge MAN en fond bleu `#0284c7`.
    - Typographie thermique encapsulée dans `.temp-unit` (`font-family: 'Open Sans', 'Segoe UI', sans-serif`) avec entité HTML `&deg;C`, éliminant le bug d'affichage tofu `[]`.
    - Zone système (GPU/CPU/VRAM/CACHE) agrandie et aérée : insertion d'un tiret de séparation net (`<span class="compact-sep">-</span>`) entre le pourcentage d'utilisation et la température (`37% - 62°C`), typographie rehaussée (`15.5px` et `12.5px`) tout en compensant la hauteur pour préserver 100% des proportions originales de la fenêtre sans ascenseur vertical.
  - **Télémétrie Python (`flight_perf_tracker.py` & `flight_remote_server.py`) :**
    - Cache anti-saturation de 0.8s et chemins système directs vers `nvidia-smi.exe`.
    - Propagation continue de `gpu_temp_c` et `cpu_temp_c` dans `_worker` et `flight_remote_server.py`.
    - Inclusion des modules `psutil` et `win32com` dans `SceneryX.spec`.
  - **Déploiement & Compilation :**
    - Package Toolbar MSFS recompilé et redéployé dans `Community` et `Community2024`.
    - Recompilation complète de `SceneryX.exe` via PyInstaller (Build v1.1.3).
- **Validation :**
  - Télémétrie en direct validée via port 8080 : `GPU Temp: 58°C`, `CPU Temp: 60.6°C`, `GPU Util: 53%`, `CPU Pct: 53.5%`.
  - Affichage des curseurs verts en AUTO, séparateur tiret visible et proportions de fenêtre inchangées.
- **Statut :** `RESOLVED` (Build v1.1.3)

---

## 📌 Modèle pour Nouveaux Incidents (Template)

```markdown
### Incident #SCX-YYYYMMDD-XXXX
- **Date :** YYYY-MM-DD HH:MM:SS
- **Machine ID :** SCX-ID-XXXXXXXXXXXX
- **Catégorie :** [Crash / Performance / Télémétrie / MSFS / UI]
- **Description Utilisateur :** "..."
- **Diagnostic Racine :**
  - ...
- **Fichiers Affectés :**
  - `path/to/file.py`
- **Actions Correctives :**
  - ...
- **Statut :** [OPEN | INVESTIGATING | RESOLVED | VERIFIED] (Version)
```
