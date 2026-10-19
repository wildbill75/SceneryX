# Design Technique : Mécanisme d'Instance Unique (Single-Instance Enforcement)

## Contexte
Afin d'éviter tout conflit d'accès concurrent aux bases de données SQLite/JSON, aux profils GSX et aux fichiers de configuration de Microsoft Flight Simulator (`Content.xml`), l'application SceneryX doit garantir qu'une seule et unique instance s'exécute à la fois sur le système.

## Architecture & Design Technique

### 1. Primitives Win32 (Named Mutex)
- **API utilisée :** `CreateMutexW` du noyau Windows (`kernel32.dll`).
- **Nom du Mutex :** `SceneryX_SingleInstance_Mutex`.
- **Comportement du noyau :**
  - Lors de la création, si `GetLastError() == ERROR_ALREADY_EXISTS` (code 183), une instance antérieure est déjà active.
  - La poignée (*handle*) est conservée au niveau du module pendant toute la durée de vie du processus maître.
  - En cas de fermeture normale ou anormale (crash, fermeture via Gestionnaire des tâches), le noyau Windows libère immédiatement et automatiquement le mutex, évitant tout blocage de verrou orphelin sur disque.

### 2. Restauration de l'Instance Active
- Recherche de la fenêtre principale existante via `FindWindowW(None, "SceneryX")`.
- Si trouvée, restauration et passage au premier plan :
  - `ShowWindow(hwnd, SW_RESTORE)` (code 9) pour désiconiser/restaurer la fenêtre si elle était minimisée.
  - `SetForegroundWindow(hwnd)` pour lui redonner le focus utilisateur.

### 3. Modale d'Avertissement Multilingue
- Affichage d'une boîte de dialogue modale native via `MessageBoxW` (`user32.dll`) avec les drapeaux :
  - `MB_OK` (0x00000000)
  - `MB_ICONWARNING` (0x00000030)
  - `MB_TOPMOST` (0x00040000) pour garantir la visibilité au premier plan.
  - `MB_SETFOREGROUND` (0x00010000).
- Adaptation automatique de la langue selon les préférences utilisateur (paramètres `language` dans `settings.json`, avec repli sur la langue de l'interface Windows) :
  - **FR :** *"SceneryX est déjà ouvert.\n\nUne seule instance de l'application peut être exécutée à la fois."*
  - **EN :** *"SceneryX is already running.\n\nOnly one instance of the application can run at a time."*
  - **DE :** *"SceneryX wird bereits ausgeführt.\n\nEs kann nur eine Instanz der Anwendung gleichzeitig ausgeführt werden."*
  - **ES :** *"SceneryX ya está abierto.\n\nSolo se puede ejecutar una instancia de la aplicación a la vez."*
- Fermeture immédiate et propre de la seconde instance avec `sys.exit(0)`.
