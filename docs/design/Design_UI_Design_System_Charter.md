# Design_UI_Design_System_Charter

## 1. Vision & Objectif d'Harmonisation Globale

Ce document constitue la **Charte de Design UI & Design System** officielle de SceneryX.  
Il fait office de **Source Unique de Vérité (SSOT)** pour l'ensemble des écrans, fenêtres modales, HUD et rapports de performance de l'application.

L'objectif est d'éliminer définitivement les disparités graphiques, le surplus décoratif et l'aspect "vibe coding" (icônes ajoutées sans discernement, effets glassmorphism / flous excessifs, gradients disparates) pour adopter une identité visuelle **sobre, chirurgicale, ergonomique et haut de gamme**, inspirée des suites logicielles professionnelles de l'aviation moderne (Navigraph, SimBrief, avionique Honeywell/Thales).

---

## 2. Principes Directeurs Inviolables (Les Règles d'Or)

1. **Zéro Icône Décorative / Zéro Pollution Visuelle** :
   - Une icône n'est autorisée que si elle remplit une **fonction d'action claire** (ex: fermer une modale, ouvrir un dossier, recharger) ou un **statut d'alerte critique**.
   - Interdiction de saupoudrer des icônes devant chaque titre de carte, chaque mot ou chaque bouton standard si un texte clair suffit.
2. **Bannissement des "Glass FX" Fantaisie** :
   - Pas de `backdrop-filter: blur()`, pas d'ombres portées multicolores, pas de reflets transparents flous sur l'application de bureau principale.
   - Les fonds sont solides et lisibles : des aplats sombres haute précision (`#0b0f19`, `#0f172a`, `#1e293b`), avec des bordures de 1px nettes et discrètes (`border-slate-850` / `#1e293b`).
3. **Typographie Rigoureuse & Hiérarchie de Données** :
   - **Chiffres, Télémétrie & Codes OACI** : Toujours en police à chasse fixe (`font-mono`), avec alignement tabulaire naturel.
   - **Libellés & Textes de Navigation** : Police moderne sans-serif sobre (`Inter`, `-apple-system`, `Segoe UI`).
   - Tailles maîtrisées : titres de cartes compacts (10-11px uppercase en `slate-400`), chiffres clés lisibles sans être disproportionnés.
4. **Intégration d'Éléments SVG Propriétaires** :
   - Abandon progressif des bibliothèques d'icônes génériques du web (FontAwesome).
   - Intégration directe des SVG sur-mesure fournis par l'utilisateur pour garantir une identité graphique 100% propriétaire, nette sur tous les écrans (4K, QHD, VR).

---

## 3. Palette Chromatique Officielle

La palette de SceneryX repose sur une base "Cockpit Dark Slate" contrastée par des accents fonctionnels précis :

| Rôle | Teinte Hexadécimale | Usage Exclusif |
| :--- | :--- | :--- |
| **Fond Principal (Background)** | `#0b0f19` (Slate 950 profond) | Arrière-plan général de l'application et des fenêtres. |
| **Fond Cartes & Conteneurs** | `#0f172a` (Slate 900) | Blocs d'informations, cartes de données et panneaux latéraux. |
| **Bordures Subtiles** | `#1e293b` (Slate 800) | Lignes de séparation de 1px, encadrements discrets. |
| **Bordures Focus / Hover** | `#334155` (Slate 700) | États survolés ou éléments sélectionnés. |
| **Texte Principal** | `#f8fafc` (Slate 50) | Chiffres clés, titres principaux, données actives. |
| **Texte Secondaire** | `#94a3b8` (Slate 400) | Libellés, sous-titres, unités de mesure, légendes. |
| **Accent Cyan Technique** | `#38bdf8` (Sky 400) | Liens, données GPS, codes OACI, badge actif. |
| **Statut Optimal (Vert)** | `#10b981` (Emerald 500) | MainThread fluide (< 22.5 ms), FPS nominaux, enregistrement actif. |
| **Statut Attention (Ambre)** | `#f59e0b` (Amber 500) | Charge modérée (MainThread 22.5-33 ms), avertissement VRAM. |
| **Statut Alerte (Rouge)** | `#ef4444` (Rose 500) | Saturation MainThread (> 33 ms), dépassement de seuil critique. |

---

## 4. Bibliothèque de Composants Standards

### 4.1. Cartes de Données (KPI Cards)
- Structure unifiée :
  - **Titre (Header)** : `10px - 11px font-mono uppercase tracking-wider text-slate-400`. Pas d'icône superflue.
  - **Valeur Principale (Moyenne)** : `text-2xl font-black text-slate-100` avec unité accolée plus petite (ex: `14.0 Go`).
  - **Sous-titre (Plage Min / Pic)** : `text-[11px] font-mono text-slate-400` (ex: `Pic : 15.3 Go • Min : 13.2 Go`).

### 4.2. Boutons d'Action (Buttons)
- **Primaire (Action Vol)** : Fond uni émeraude ou ambre sombre sans dégradé criard, bordure nette, texte contrasté.
- **Secondaire / Utilitaire** : Fond `slate-900`, bordure `slate-700`, texte `slate-300`, survol `slate-800`.
- **Danger (Suppression / Déconnexion)** : Fond `rose-950/40`, bordure `rose-800`, texte `rose-200`.

### 4.3. Badges & Statuts (Pills)
- Format compact : `px-2 py-0.5 rounded-md text-[10px] font-mono uppercase font-bold`.
- Fond semi-transparent à 15% de la couleur d'accent + bordure solide de 1px.

---

## 5. Gestion et Intégration des SVG Personnalisés

Lorsque des fichiers SVG personnalisés sont fournis :
1. **Emplacement de Stockage** : `web/assets/icons/`
2. **Normalisation SVG** :
   - `viewBox="0 0 24 24"` ou format vectoriel cohérent.
   - Suppression des couleurs en dur (`fill="#..."` remplacé par `fill="currentColor"` ou `stroke="currentColor"`).
   - Cela permet au composant d'hériter directement des couleurs CSS Tailwind de son conteneur (`text-slate-400 hover:text-cyan-400`).
3. **Composant Loader / Inline** :
   - Insertion soit via un injecteur direct, soit sous forme de petits fragments HTML réutilisables, évitant tout délai de chargement ou scintillement.

---

## 6. Protocole de Non-Régression pour les Futurs Développements

Pour garantir qu'aucun écart ne soit commis lors des futurs ajouts :
1. **Contrôle Avant Validation** :
   - Toute nouvelle interface doit être confrontée à cette charte.
   - Interdiction formelle d'ajouter des effets "glass" ou des icônes automatiques si elles ne figurent pas dans la maquette demandée.
2. **Consignation Permanente dans l'Agent** :
   - Inscription de ces interdits dans les règles permanentes de l'environnement de développement pour guider automatiquement chaque intervention de code.
