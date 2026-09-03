# SceneryX — Next-Generation MSFS Scenery & Flight Operations Manager

[![Version](https://img.shields.io/badge/version-1.0.1--BETA-cyan.svg)](https://github.com/wildbill75/SceneryX)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-blue.svg)](https://github.com/wildbill75/SceneryX)
[![Simulator](https://img.shields.io/badge/MSFS-2020%20%7C%202024-emerald.svg)](https://www.flightsimulator.com/)
[![License](https://img.shields.io/badge/license-Freeware%20%2F%20Personal%20Use-purple.svg)](#legal--disclaimers)

---

## Language Selection / Sélection de la langue / Sprachauswahl / Selección de idioma
- [English Documentation](#-english)
- [Documentation en Français](#-français)
- [Deutsche Dokumentation](#-deutsch)
- [Documentación en Español](#-español)
- [Legal Mentions & Disclaimers / Mentions Légales](#-legal-mentions--disclaimers)

---

# 🇬🇧 English

## 1. Overview
**SceneryX** is a modern, high-performance desktop suite designed specifically for Microsoft Flight Simulator (MSFS 2020 and MSFS 2024) pilots and enthusiasts. It bridges the gap between scenery library management, collection financial tracking, real-time marketplace price comparison, live weather briefings, and flight plan route optimization (SimBrief).

Built with a native single-executable architecture and an ultra-responsive dark glassmorphism cockpit interface, SceneryX empowers flight simmers to catalog, inspect, audit, and optimize hundreds of installed airport add-ons seamlessly.

---

## 2. Key Features

### 🗺️ Interactive Global 3D/2D Airport Map
- **Leaflet & MarkerCluster Integration**: Dynamically visualizes all installed sceneries globally with fluid cluster breakdown by region and airport density.
- **Cinematic Camera Control**: Smooth camera pan and zoom transitions with user-customizable speed (*Fast*, *Smooth*, *Cinematic*) and default airport zoom depth (*Wide*, *Regional*, *Runway*).
- **Customizable Startup Viewport**: Choose your default opening geographical focus (*World*, *Western Europe*, *North America*, *Asia*, *Oceania*, etc.) in Settings.
- **Rich Hover & Focus Previews**: Hover over any airport marker to inspect ICAO, city, country, status (Payware, Freeware, Asobo), and active GSX profile presence.

### 🔍 Deep Dual Simulator Scanning (MSFS 2020 & 2024)
- **Multi-Path Configurator**: Scans local `Community` folders, `Official` packages, and MSFS 2024 `StreamedPackages` (cloud-streamed assets).
- **Flexible Path Management**: Add, name, enable, or disable custom scenery folders independently.
- **Accurate Metadata Extraction**: Reads layout files, manifest files, airport coordinates, runways, and package identity.
- **GSX Pro Profile Auto-Matching**: Automatically detects and links your `.ini` GSX aircraft/airport ground handling profiles located in `%APPDATA%\Virtuali\GSX\MSFS`.

### 💰 Financial & Collection Investment Dashboard
- **Total Spent Overview**: Live summary banner calculating your cumulative investment across all payware sceneries.
- **Multi-Currency System**: Switch seamlessly between **USD ($)**, **EUR (€)**, **GBP (£)**, and **AUD (A$)** in Settings; all monetary values across the entire application update reactively.
- **Custom Price Override**: Manually adjust the price paid for any airport (individual purchases, discounts, or bundles) via the airport details drawer.
- **Country Investment Drawer**: Drill down by country to inspect total spending, total airports owned, and a dedicated list of sceneries with one-click map focus.

### 🛒 Live Payware Store Price Comparator
- **Multi-Store Aggregator**: Live product availability and price query across 15+ flight simulation marketplaces and official developer stores (*simMarket, Orbx Direct, Flightbeam Studios, iniBuilds Store, Aerosoft Shop, France VFR, FlyTampa, FSDreamTeam, Jetstream Designs, LatinVFR, Pyreegue Dev Co., NZA Simulations, Drzewiecki Design, Contrail, Flightsim.to*).
- **Cheapest First (Ascending Sort)**: Automatically sorts matching stores from lowest price to highest price in your selected currency.
- **Official Developer Studio Recognition (`👑 [OFFICIAL DEV]`)**: Highlights official developer stores with golden badges and elevates them when prices are competitive.
- **Smart Anti-False-Positive Engine**: Rigorously excludes vintage/retro packages (e.g. *1935 Geneva*), city landmark packs (e.g. *Paris Landmarks*), GSX profile packs, liveries, textures, night lighting packs, and legacy simulator versions (*FSX*, *P3D*, *X-Plane*).
- **Non-Closing Modal Workflow**: Keeps the comparator modal open when clicking external links to let you cross-check multiple vendors without interruption.

### 🌦️ Live Weather & ACARS Briefings
- **Structured Briefing Engine**: Retrieves live METAR and TAF reports for departure, destination, and alternate stations.
- **Pilot Telemetry Badges**: Key variables (QNH, Wind Direction & Speed, Visibility, Cloud Base, Temperature/Dew point) isolated as color-coded pills.
- **Operational Commentary**: Runway selection advice and pilot-style weather summaries.
- **Periodic ACARS Refresh**: Background update loop continuously refreshing weather conditions without flickering.

### ⚡ SimBrief Flight Route Optimizer
- **Direct SimBrief Dispatch Import**: Pull your latest flight plan using your SimBrief Pilot ID or username.
- **VRAM & Memory Scenery Isolation**: Temporarily disables unused third-party sceneries worldwide while preserving Origin, Destination, and Alternates, drastically reducing simulator loading times and memory usage.

### 📤 Multi-Format Exports & Backups
- **CSV Spreadsheet**: Export your entire catalog or active filtered view into an Excel-, Volanta-, and Elevatex-compatible CSV.
- **JSON Full Backup**: Export complete raw structured metadata for database backup or custom integration.

### 🖥️ Native Display & Ergonomics
- **Display Resolution Adaptation**: Detects primary monitor resolution (1080p, 1440p / 2K, 2160p / 4K) and scales window proportions automatically.
- **Balanced Geometry**: Calculates symmetrical margins taking into account the Windows taskbar for visual centering.
- **4 Full Languages**: English, Français, Deutsch, and Español.

---

# 🇫🇷 Français

## 1. Présentation
**SceneryX** est une suite logicielle de bureau moderne et performante conçue pour les pilotes et passionnés de Microsoft Flight Simulator (MSFS 2020 et MSFS 2024). Elle réunit au sein d'une même interface la gestion de votre bibliothèque de scènes, le suivi financier de vos investissements, la comparaison en direct des prix sur les boutiques spécialisées, les briefings météo ACARS et l'optimisation des scènes selon votre plan de vol SimBrief.

Distribué sous forme d'un exécutable unique autonome et doté d'une interface sombre style cockpit en verre dépoli (glassmorphism), SceneryX vous permet d'auditer, cataloguer et organiser des centaines d'aéroports en toute simplicité.

---

## 2. Fonctionnalités Principales

### 🗺️ Carte Globale Interactive 3D/2D
- **Intégration Leaflet & MarkerCluster** : Affichage fluide de tous vos aéroports installés avec regroupement dynamique par grappes selon la région et le zoom.
- **Caméra Cinématique** : Transitions de panoramique et de zoom ultra-fluides avec vitesse réglable (*Rapide*, *Fluide*, *Cinématique*) et niveau de zoom par défaut (*Large*, *Régional*, *Piste*).
- **Région de Démarrage Personnalisable** : Définissez votre cadrage géographique initial (*Monde*, *Europe de l'Ouest*, *Amérique du Nord*, *Asie*, *Océanie*, etc.).
- **Infobulles au Survol** : Survolez n'importe quel aéroport pour consulter son code OACI, sa ville, son pays, son type (Payware, Freeware, Asobo) et la présence d'un profil GSX actif.

### 🔍 Analyse Approfondie Multi-Simulateurs (MSFS 2020 & 2024)
- **Gestionnaire Multi-Répertoires** : Analyse les dossiers `Community`, `Official` et les scènes en streaming de MSFS 2024 (`StreamedPackages`).
- **Personnalisation des Chemins** : Ajoutez des dossiers personnalisés, nommez-les et activez/désactivez leur analyse à la demande.
- **Extraction Précise des Données** : Lecture des manifestes, coordonnées GPS, orientation des pistes et métadonnées du package.
- **Liaison Automatique GSX Pro** : Détecte automatiquement les profils de manutention au sol `.ini` présents dans `%APPDATA%\Virtuali\GSX\MSFS`.

### 💰 Suivi Financier & Tableau de Bord d'Investissement
- **Bannière d'Investissement Global** : Calcul instantané du montant cumulé dépensé sur l'ensemble de vos scènes paywares.
- **Gestion Multi-Devises** : Basculez entre **USD ($)**, **EUR (€)**, **GBP (£)** et **AUD (A$)** dans les Paramètres ; tous les chiffres et symboles se mettent à jour instantanément.
- **Personnalisation du Prix d'Achat** : Ajustez manuellement le tarif payé pour chaque aéroport (promotions, achats groupés) via le volet latéral.
- **Tiroir d'Investissement par Pays** : Classement par pays affichant le montant total investi, le nombre de plateformes possédées et la liste cliquable des scènes.

### 🛒 Comparateur de Prix & Boutiques Officielles en Direct
- **Agrégateur Multi-Boutiques** : Interrogation en temps réel de plus de 15 boutiques spécialisées et studios créateurs (*simMarket, Orbx Direct, Flightbeam Studios, iniBuilds Store, Aerosoft Shop, France VFR, FlyTampa, FSDreamTeam, Jetstream Designs, LatinVFR, Pyreegue Dev Co., NZA Simulations, Drzewiecki Design, Contrail, Flightsim.to*).
- **Tri du Moins Cher au Plus Cher** : Classement automatique par tarif croissant dans la devise de votre choix.
- **Reconnaissance des Studios Officiels (`👑 [OFFICIAL DEV]`)** : Mise en valeur des boutiques officielles avec badge doré et couronne.
- **Moteur Anti-Faux-Positifs** : Écarte automatiquement les scènes d'époque (*Genève 1935*), les packs de monuments/villes (*Paris Landmarks*), les livrées, textures, sons, profils GSX et versions pour anciens simulateurs (*FSX*, *P3D*, *X-Plane*).
- **Navigation Continue** : La modale reste ouverte lors d'un clic pour vous permettre d'ouvrir plusieurs boutiques en parallèle.

### 🌦️ Briefing Météo & Télégrammes ACARS
- **Moteur de Briefing Structuré** : Récupération des rapports METAR et TAF pour les stations de départ, d'arrivée et de déroutement.
- **Badges Télémétriques** : QNH, Vent, Visibilité, Plafond nuageux et Température mis en évidence.
- **Conseils Opérationnels** : Recommandations de piste en service et commentaires narratifs type pilote de ligne.
- **Rafraîchissement Arrière-Plan** : Mise à jour périodique transparente sans scintillement d'interface.

### ⚡ Optimiseur de Scènes SimBrief
- **Import Direct SimBrief** : Récupération de votre dernier plan de vol via votre identifiant pilote ou nom d'utilisateur.
- **Isolation Mémoire & VRAM** : Désactive temporairement les scènes tierces superflues tout en conservant l'origine, la destination et les dégagements, accélérant drastiquement le chargement du simulateur.

### 📤 Sauvegardes & Exports Multi-Formats
- **Export Tableur CSV** : Fichier tableur complet compatible avec Excel, Google Sheets, Volanta et Elevatex.
- **Sauvegarde JSON Complète** : Export structuré de l'intégralité de vos métadonnées pour archivage ou automatisation.

### 🖥️ Ergonomie & Affichage Natif
- **Détection Automatique de la Résolution** : Adaptation sur écrans 1080p, 1440p (2K) et 4K.
- **Centrage au Pixel Près** : Calcul des marges horizontales et verticales prenant en compte la barre des tâches Windows.
- **4 Langues Disponibles** : Français, Anglais, Allemand et Espagnol.

---

# 🇩🇪 Deutsch

## 1. Übersicht
**SceneryX** ist eine moderne, hochperformante Desktop-Suite für Microsoft Flight Simulator (MSFS 2020 und MSFS 2024). Sie vereint Szenerieverwaltung, finanzielle Erfassung Ihrer Add-on-Ausgaben, Echtzeit-Preisvergleiche führender Flugsimulations-Shops, ACARS-Wetterbriefings und SimBrief-Flugstrecken-Optimierung in einer eleganten Benutzeroberfläche.

Als eigenständige ausführbare Datei mit dunklem Glasmorphismus-Cockpit-Design konzipiert, bietet SceneryX vollständige Übersicht und Kontrolle über Hunderte von Flughafenszenerien.

---

## 2. Hauptfunktionen

### 🗺️ Interaktive Globale 3D/2D-Weltkarte
- **Leaflet & MarkerCluster**: Dynamische Visualisierung aller installierten Flughäfen weltweit mit intelligenter Gruppierung.
- **Kinematische Kamerasteuerung**: Weiche Kamerafahrten mit anpassbarer Geschwindigkeit (*Schnell*, *Sanft*, *Kinematisch*) und Standard-Zoomtiefe (*Weit*, *Regional*, *Landebahn*).
- **Einstellbare Startregion**: Definieren Sie Ihren bevorzugten geografischen Einstiegspunkt (*Welt*, *Westeuropa*, *Nordamerika*, *Asien*, *Ozeanien* usw.) in den Einstellungen.
- **Detaillierte Vorschau**: Überfahren Sie Marker mit der Maus, um ICAO-Code, Stadt, Land, Typ (Payware, Freeware, Asobo) und GSX-Profile einzusehen.

### 🔍 Umfassender Scan für MSFS 2020 & 2024
- **Multi-Pfad-Verwaltung**: Scannt `Community`-, `Official`- und MSFS 2024 `StreamedPackages`-Verzeichnisse.
- **Benutzerdefinierte Pfade**: Beliebige Ordner hinzufügen, benennen und aktivieren oder deaktivieren.
- **Exakte Metadaten**: Auslesen von Layouts, Koordinaten, Start- und Landebahnen und Paketdaten.
- **Automatische GSX Pro Profilzuordnung**: Erkennt verknüpfte `.ini`-Profile in `%APPDATA%\Virtuali\GSX\MSFS`.

### 💰 Finanz- und Sammlungs-Dashboard
- **Gesamtausgaben-Übersicht**: Live-Anzeige der kumulierten Gesamtausgaben aller Payware-Szenerien.
- **Multi-Währungssystem**: Umschalten zwischen **USD ($)**, **EUR (€)**, **GBP (£)** und **AUD (A$)**; alle Beträge in der Anwendung werden sofort umgerechnet.
- **Manueller Preisabgleich**: Überschreiben Sie bezahlte Preise für individuelle Angebote oder Bundles in den Flughafendetails.
- **Länder-Investitionsansicht**: Detaillierte Länderanalyse mit Gesamtausgaben, Anzahl der Flughäfen und Direktfokus auf der Karte.

### 🛒 Live-Shop-Preisvergleich & Entwickler-Stores
- **Multi-Shop-Aggregator**: Echtzeit-Verfügbarkeits- und Preisprüfung bei über 15 Stores (*simMarket, Orbx Direct, Flightbeam Studios, iniBuilds Store, Aerosoft Shop, France VFR, FlyTampa, FSDreamTeam, Jetstream Designs, LatinVFR, Pyreegue, NZA Simulations, Drzewiecki Design, Contrail, Flightsim.to*).
- **Günstigster Preis zuerst**: Automatische Sortierung aufsteigend nach dem besten Preis in Ihrer gewählten Währung.
- **Hervorhebung Offizieller Studios (`👑 [OFFICIAL DEV]`)**: Goldene Abzeichen für direkte Entwickler-Websites.
- **Intelligenter Falsch-Positiv-Filter**: Schließt historische Retro-Szenerien (*Genf 1935*), Stadt-Wahrzeichen (*Paris Landmarks*), Lackierungen, Profile und ältere Simulatoren (*FSX*, *P3D*, *X-Plane*) zuverlässig aus.
- **Paralleles Stöbern**: Das Vergleichsfenster bleibt nach dem Klick geöffnet für bequemes Vergleichen im Browser.

### 🌦️ Live-Wetter & ACARS-Briefings
- **Strukturiertes Briefing**: METAR- und TAF-Berichte für Abflug-, Ziel- und Ausweichflughäfen.
- **Piloten-Badges**: QNH, Windrichtung/-stärke, Sichtweite, Wolkenuntergrenze und Temperatur übersichtlich dargestellt.
- **Bahnempfehlungen**: Berechnete Landebahnempfehlungen und operationelle Kommentare.
- **Periodische Aktualisierung**: Kontinuierliche Hintergrundaktualisierung ohne Benutzeroberflächen-Flackern.

### ⚡ SimBrief-Streckenoptimierer
- **SimBrief-Import**: Direkter Import des letzten Flugplans mittels Pilot-ID oder Benutzername.
- **Speicher- und VRAM-Optimierung**: Deaktiviert ungenutzte weltweite Szenerien temporär und behält Abflug, Ankunft und Ausweichflughäfen bei für maximale Ladeleistung.

### 📤 Exporte & Datensicherung
- **CSV-Export**: Kompatibel mit Excel, Google Tabellen, Volanta und Elevatex.
- **JSON-Komplettsicherung**: Vollständiger strukturierter Metadatenexport für Backups und Werkzeuge.

### 🖥️ Anzeige & Ergonomie
- **Automatische Auflösungserkennung**: Automatische Größenanpassung auf 1080p-, 1440p (2K)- und 4K-Monitoren.
- **Perfekt Zentriert**: Exakt berechnete Ränder unter Berücksichtigung der Windows-Taskleiste.
- **4 Vollständige Sprachen**: Deutsch, Englisch, Französisch und Spanisch.

---

# 🇪🇸 Español

## 1. Resumen
**SceneryX** es una suite de escritorio moderna y de alto rendimiento diseñada específicamente para pilotos y aficionados de Microsoft Flight Simulator (MSFS 2020 y MSFS 2024). Integra en un único entorno la gestión de bibliotecas de escenarios, el control de inversión financiera en complementos, la comparación de precios en tiendas especializadas en tiempo real, informes meteorológicos ACARS y la optimización de rutas de vuelo mediante SimBrief.

Distribuido como un archivo ejecutable único con una interfaz oscura estilo cabina en vidrio esmerilado (glassmorphism), SceneryX facilita la organización y auditoría de cientos de aeropuertos instalados.

---

## 2. Características Principales

### 🗺️ Mapa Global Interactivo 3D/2D
- **Integración Leaflet & MarkerCluster**: Visualización fluida de todos los aeropuertos instalados con agrupación dinámica por regiones.
- **Control Cinemático de Cámara**: Movimientos suaves de desplazamiento y zoom con velocidad configurable (*Rápido*, *Suave*, *Cinemático*) y profundidad de zoom predeterminada (*Amplio*, *Regional*, *Pista*).
- **Región Inicial Configurable**: Seleccione su encuadre geográfico predeterminado (*Mundo*, *Europa Occidental*, *Norteamérica*, *Asia*, *Oceanía*, etc.).
- **Vistas Previas al Pasar el Cursor**: Consulte código OACI, ciudad, país, categoría (Payware, Freeware, Asobo) y perfiles GSX activos.

### 🔍 Escaneo Profundo Multi-Simulador (MSFS 2020 & 2024)
- **Gestor Multi-Directorio**: Escanea carpetas `Community`, `Official` y paquetes transmitidos de MSFS 2024 (`StreamedPackages`).
- **Rutas Personalizadas**: Añada, nombre y active o desactive carpetas según sus necesidades.
- **Metadatos Precisos**: Extracción de pistas, coordenadas geográficas y datos de manifiesto.
- **Detección Automática de Perfiles GSX Pro**: Vincula automáticamente los perfiles `.ini` ubicados en `%APPDATA%\Virtuali\GSX\MSFS`.

### 💰 Panel de Control Financiero y Colección
- **Gasto Total Acumulado**: Indicador superior en tiempo real con la suma total invertida en escenarios de pago.
- **Sistema Multidivisa**: Cambie entre **USD ($)**, **EUR (€)**, **GBP (£)** y **AUD (A$)**; todos los importes y símbolos se recalculan de inmediato.
- **Precio Personalizable**: Modifique el importe pagado por cada aeropuerto (ofertas, paquetes) en la ficha técnica.
- **Desglose por País**: Consulta de inversión total, cantidad de aeropuertos y lista interactiva con enfoque directo en el mapa.

### 🛒 Comparador de Precios en Tiendas Oficiales
- **Agregador de Tiendas en Vivo**: Consulta en tiempo real en más de 15 tiendas y estudios oficiales (*simMarket, Orbx Direct, Flightbeam Studios, iniBuilds Store, Aerosoft Shop, France VFR, FlyTampa, FSDreamTeam, Jetstream Designs, LatinVFR, Pyreegue, NZA Simulations, Drzewiecki Design, Contrail, Flightsim.to*).
- **Orden Ascendente (Más Barato Primero)**: Ordena automáticamente las tiendas desde el precio más económico.
- **Reconocimiento de Estudios Oficiales (`👑 [OFFICIAL DEV]`)**: Distintivo dorado para tiendas oficiales de los desarrolladores.
- **Filtro Inteligente Anti-Falsos Positivos**: Bloquea paquetes retro (*Ginebra 1935*), monumentos urbanos (*Paris Landmarks*), libreas, texturas, perfiles GSX y simuladores anteriores (*FSX*, *P3D*, *X-Plane*).
- **Consulta Continua**: La ventana emergente no se cierra al abrir un enlace, permitiendo contrastar varias ofertas simultáneamente.

### 🌦️ Informes Meteorológicos y ACARS
- **Motor de Briefing Estructurado**: Recepción de METAR y TAF para salida, llegada y alternativas.
- **Insignias Telemétricas**: QNH, Viento, Visibilidad, Techo de nubes y Temperatura destacados visualmente.
- **Consejos de Pista**: Sugerencias operativas de pistas activas y comentarios estilo piloto comercial.
- **Actualización en Segundo Plano**: Bucle periódico transparente sin parpadeos visuales.

### ⚡ Optimizador de Escenarios SimBrief
- **Importación Directa SimBrief**: Carga instantánea del último plan de vuelo mediante ID de piloto o usuario.
- **Aislamiento de Memoria y VRAM**: Desactiva temporalmente escenarios innecesarios conservando origen, destino y alternativas para acelerar la carga del simulador.

### 📤 Exportación y Copias de Seguridad
- **Hoja de Cálculo CSV**: Exportación compatible con Excel, Google Sheets, Volanta y Elevatex.
- **Copia de Seguridad JSON**: Exportación estructurada de metadatos completos para respaldo.

### 🖥️ Ergonomía y Visualización
- **Detección Automática de Pantalla**: Adaptación a resoluciones 1080p, 1440p (2K) y 4K.
- **Centrado al Píxel**: Márgenes calculados equilibrados teniendo en cuenta la barra de tareas de Windows.
- **4 Idiomas Completos**: Español, Inglés, Francés y Alemán.

---

# ⚖️ Legal Mentions & Disclaimers

### 1. General Disclaimer / Clause de Non-Responsabilité / Haftungsausschluss / Exención de Responsabilidad
SceneryX is an independent, non-commercial software suite provided on an **"AS IS"** and **"AS AVAILABLE"** basis, without warranty of any kind, either express or implied, including but not limited to the implied warranties of merchantability, fitness for a particular purpose, or non-infringement.

The authors and copyright holders shall in no event be held liable for any claim, damages, data loss, file system corruption, simulator instability, or other liability arising from, out of, or in connection with the software or the use or other dealings in the software. Users interact with simulator configurations, `Community` packages, and `Content.xml` entirely at their own discretion and risk.

### 2. Trademark Notices & Non-Affiliation
- **Microsoft®**, **Microsoft Flight Simulator®**, **MSFS 2020**, **MSFS 2024**, **Windows®**, and the Windows Logo are registered trademarks or trademarks of Microsoft Corporation in the United States and/or other countries.
- **Asobo Studio®** is a registered trademark of Asobo Studio SAS.
- **Lockheed Martin®** and **Prepar3D®** are registered trademarks of Lockheed Martin Corporation.
- **Laminar Research®** and **X-Plane®** are registered trademarks of Laminar Research.
- **SimBrief®** and **Navigraph®** are registered trademarks of Navigraph Sweden AB.
- **GSX Pro®** and **FSDreamTeam®** are registered trademarks of VIRTUALI s.a.s.
- **simMarket®**, **Orbx®**, **Aerosoft®**, **iniBuilds®**, **Flightbeam®**, **FlyTampa®**, **Flightsim.to®**, **France VFR®**, and other third-party vendor names and logos are trademarks of their respective owners.
- **SceneryX is an independent community project and is NOT affiliated with, authorized, sponsored, or endorsed by Microsoft Corporation, Asobo Studio, or any third-party developer or storefront mentioned.**

### 3. Data Privacy & Local Processing
- **100% Local Processing**: SceneryX does NOT collect, harvest, store, or transmit any personal identifying information, simulator telemetry, credentials, or analytical data.
- **External Web Queries**: Network traffic generated by SceneryX is strictly restricted to:
  - Public SimBrief XML dispatch retrieval (upon user manual request).
  - Public NOAA / VATSIM / Active Sky METAR & TAF meteorological feeds.
  - Public search endpoints of flight simulation storefronts (to check add-on availability and pricing).
- No user data is stored on remote servers; all settings and library databases reside strictly on your local machine (`%APPDATA%\SceneryX` and application directory).

### 4. License & Redistribution
SceneryX is distributed for free personal, non-commercial use. Modifying, reverse-engineering, decompiling, or redistributing the software for commercial gain without explicit prior written authorization from the copyright owner is prohibited.

---
*Developed with precision for the global flight simulation community.*
