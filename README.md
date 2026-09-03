================================================================================
SCENERYX — Next-Generation MSFS Scenery & Collection Manager
================================================================================

Version   : 1.0.1-BETA
Platform  : Windows 10 / Windows 11 (64-bit)
Simulator : Microsoft Flight Simulator 2020 & 2024
License   : Freeware / Personal Non-Commercial Use
Website   : https://github.com/wildbill75/SceneryX

================================================================================
SOMMAIRE / TABLE OF CONTENTS
================================================================================
1. English Documentation
2. Documentation en Français
3. Deutsche Dokumentation
4. Documentación en Español
5. Legal Mentions & Disclaimers / Mentions Légales

================================================================================
1. ENGLISH DOCUMENTATION
================================================================================

1.1 OVERVIEW
SceneryX is a modern, high-performance desktop suite designed specifically 
for Microsoft Flight Simulator (MSFS 2020 and MSFS 2024) pilots and enthusiasts. 
It bridges the gap between scenery library management, collection financial 
tracking, and real-time marketplace price comparison across major flight 
simulation stores.

Built with a native single-executable architecture and an ultra-responsive 
dark cockpit interface, SceneryX empowers flight simmers to catalog, inspect, 
audit, and organize hundreds of installed airport add-ons seamlessly.

1.2 KEY FEATURES

* Interactive Global 3D/2D Airport Map:
  - Leaflet & MarkerCluster integration dynamically visualizes all installed 
    sceneries globally with fluid cluster breakdown by region and airport density.
  - Smooth camera pan and zoom transitions with user-customizable speed 
    (Fast, Smooth, Cinematic) and default airport zoom depth (Wide, Regional, Runway).
  - Customizable startup viewport: choose your default opening focus (World, 
    Western Europe, North America, Asia, Oceania, etc.) in Settings.
  - Rich hover previews: inspect ICAO, city, country, status (Payware, Freeware, 
    Asobo), and active GSX profile presence.

* Deep Dual Simulator Scanning (MSFS 2020 & 2024):
  - Scans local Community folders, Official packages, and MSFS 2024 
    StreamedPackages (cloud-streamed assets).
  - Multi-path configurator: add, name, enable, or disable custom scenery 
    folders independently.
  - Accurate metadata extraction: reads layout files, manifest files, airport 
    coordinates, runways, and package identity.
  - GSX Pro profile auto-matching: automatically detects and links your .ini 
    GSX ground handling profiles located in %APPDATA%\Virtuali\GSX\MSFS.

* Financial & Collection Investment Dashboard:
  - Live summary banner calculating your cumulative investment across all payware sceneries.
  - Multi-currency system: switch seamlessly between USD ($), EUR (€), GBP (£), 
    and AUD (A$) in Settings; all monetary values across the entire application update reactively.
  - Custom price override: manually adjust the price paid for any airport 
    (individual purchases, discounts, bundles) via the airport details drawer.
  - Country investment drawer: drill down by country to inspect total spending, 
    total airports owned, and a dedicated list of sceneries with one-click map focus.

* Live Payware Store Price Comparator:
  - Live product availability and price query across 15+ flight simulation 
    marketplaces and official developer stores (simMarket, Orbx Direct, 
    Flightbeam Studios, iniBuilds Store, Aerosoft Shop, France VFR, FlyTampa, 
    FSDreamTeam, Jetstream Designs, LatinVFR, Pyreegue Dev Co., NZA Simulations, 
    Drzewiecki Design, Contrail, Flightsim.to).
  - Cheapest first (ascending sort): automatically sorts matching stores from 
    lowest price to highest price in your selected currency.
  - Official developer studio recognition [OFFICIAL DEV]: highlights official 
    developer stores with golden badges and elevates them when prices are competitive.
  - Smart anti-false-positive engine: rigorously excludes vintage/retro packages 
    (e.g. 1935 Geneva), city landmark packs (e.g. Paris Landmarks), GSX profile packs, 
    liveries, textures, night lighting packs, and legacy simulator versions (FSX, P3D, X-Plane).
  - Non-closing modal workflow: keeps the comparator modal open when clicking external 
    links to let you cross-check multiple vendors without interruption.

* Multi-Format Exports & Backups:
  - CSV spreadsheet: export your entire catalog or active filtered view into an 
    Excel-, Volanta-, and Elevatex-compatible CSV.
  - JSON full backup: export complete raw structured metadata for database backup 
    or custom automation.

* Native Display & Ergonomics:
  - Display resolution adaptation: detects primary monitor resolution (1080p, 1440p / 2K, 
    2160p / 4K) and scales window proportions automatically.
  - Balanced geometry: calculates symmetrical margins taking into account the Windows 
    taskbar for pixel-perfect visual centering.
  - 4 full languages: English, Français, Deutsch, and Español.

================================================================================
2. DOCUMENTATION EN FRANÇAIS
================================================================================

2.1 PRÉSENTATION
SceneryX est une suite logicielle de bureau moderne et performante conçue pour 
les pilotes et passionnés de Microsoft Flight Simulator (MSFS 2020 et MSFS 2024). 
Elle réunit au sein d'une même interface la gestion de votre bibliothèque de scènes, 
le suivi financier de vos investissements et la comparaison en direct des prix 
sur les principales boutiques spécialisées.

Distribué sous forme d'un exécutable unique autonome et doté d'une interface sombre 
style cockpit en verre dépoli (glassmorphism), SceneryX vous permet d'auditer, 
cataloguer et organiser des centaines d'aéroports en toute simplicité.

2.2 FONCTIONNALITÉS PRINCIPALES

* Carte Globale Interactive 3D/2D :
  - Intégration Leaflet & MarkerCluster : affichage fluide de tous vos aéroports 
    installés avec regroupement dynamique par grappes selon la région et le zoom.
  - Caméra cinématique : transitions de panoramique et de zoom ultra-fluides avec 
    vitesse réglable (Rapide, Fluide, Cinématique) et niveau de zoom par défaut 
    (Large, Régional, Piste).
  - Région de démarrage personnalisable : définissez votre cadrage géographique 
    initial (Monde, Europe de l'Ouest, Amérique du Nord, Asie, Océanie, etc.).
  - Infobulles au survol : survolez n'importe quel aéroport pour consulter son 
    code OACI, sa ville, son pays, son type (Payware, Freeware, Asobo) et la 
    présence d'un profil GSX actif.

* Analyse Approfondie Multi-Simulateurs (MSFS 2020 & 2024) :
  - Gestionnaire multi-répertoires : analyse les dossiers Community, Official 
    et les scènes en streaming de MSFS 2024 (StreamedPackages).
  - Personnalisation des chemins : ajoutez des dossiers personnalisés, nommez-les 
    et activez ou désactivez leur analyse à la demande.
  - Extraction précise des données : lecture des manifestes, coordonnées GPS, 
    orientation des pistes et métadonnées du package.
  - Liaison automatique GSX Pro : détecte automatiquement les profils de 
    manutention au sol .ini présents dans %APPDATA%\Virtuali\GSX\MSFS.

* Suivi Financier & Tableau de Bord d'Investissement :
  - Bannière d'investissement global : calcul instantané du montant cumulé 
    dépensé sur l'ensemble de vos scènes paywares.
  - Gestion multi-devises : basculez entre USD ($), EUR (€), GBP (£) et AUD (A$) 
    dans les Paramètres ; tous les chiffres et symboles se mettent à jour instantanément.
  - Personnalisation du prix d'achat : ajustez manuellement le tarif payé pour 
    chaque aéroport (promotions, achats groupés) via le volet latéral.
  - Tiroir d'investissement par pays : classement par pays affichant le montant 
    total investi, le nombre de plateformes possédées et la liste cliquable des scènes.

* Comparateur de Prix & Boutiques Officielles en Direct :
  - Agrégateur multi-boutiques : interrogation en temps réel de plus de 15 boutiques 
    spécialisées et studios créateurs (simMarket, Orbx Direct, Flightbeam Studios, 
    iniBuilds Store, Aerosoft Shop, France VFR, FlyTampa, FSDreamTeam, Jetstream Designs, 
    LatinVFR, Pyreegue Dev Co., NZA Simulations, Drzewiecki Design, Contrail, Flightsim.to).
  - Tri du moins cher au plus cher : classement automatique par tarif croissant 
    dans la devise de votre choix.
  - Reconnaissance des studios officiels [OFFICIAL DEV] : mise en valeur des boutiques 
    officielles avec badge doré et couronne.
  - Moteur anti-faux-positifs : écarte automatiquement les scènes d'époque (Genève 1935), 
    les packs de monuments/villes (Paris Landmarks), les livrées, textures, sons, 
    profils GSX et versions pour anciens simulateurs (FSX, P3D, X-Plane).
  - Navigation continue : la modale reste ouverte lors d'un clic pour vous permettre 
    d'ouvrir plusieurs boutiques en parallèle.

* Sauvegardes & Exports Multi-Formats :
  - Export tableur CSV : fichier tableur complet compatible avec Excel, Google Sheets, 
    Volanta et Elevatex.
  - Sauvegarde JSON complète : export structuré de l'intégralité de vos métadonnées 
    pour archivage ou automatisation.

* Ergonomie & Affichage Natif :
  - Détection automatique de la résolution : adaptation sur écrans 1080p, 1440p (2K) et 4K.
  - Centrage au pixel près : calcul des marges horizontales et verticales prenant 
    en compte la barre des tâches Windows.
  - 4 langues disponibles : Français, Anglais, Allemand et Espagnol.

================================================================================
3. DEUTSCHE DOKUMENTATION
================================================================================

3.1 ÜBERSICHT
SceneryX ist eine moderne, hochperformante Desktop-Suite für Microsoft Flight 
Simulator (MSFS 2020 und MSFS 2024). Sie vereint Szenerieverwaltung, finanzielle 
Erfassung Ihrer Add-on-Ausgaben und Echtzeit-Preisvergleiche führender 
Flugsimulations-Shops in einer eleganten Benutzeroberfläche.

Als eigenständige ausführbare Datei mit dunklem Cockpit-Design konzipiert, 
bietet SceneryX vollständige Übersicht und Kontrolle über Hunderte von 
Flughafenszenerien.

3.2 HAUPTFUNKTIONEN

* Interaktive Globale 3D/2D-Weltkarte:
  - Leaflet & MarkerCluster: dynamische Visualisierung aller installierten 
    Flughäfen weltweit mit intelligenter Gruppierung.
  - Kinematische Kamerasteuerung: weiche Kamerafahrten mit anpassbarer 
    Geschwindigkeit (Schnell, Sanft, Kinematisch) und Standard-Zoomtiefe (Weit, Regional, Landebahn).
  - Einstellbare Startregion: definieren Sie Ihren bevorzugten geografischen 
    Einstiegspunkt (Welt, Westeuropa, Nordamerika, Asien, Ozeanien usw.) in den Einstellungen.
  - Detaillierte Vorschau: überfahren Sie Marker mit der Maus, um ICAO-Code, Stadt, 
    Land, Typ (Payware, Freeware, Asobo) und GSX-Profile einzusehen.

* Umfassender Scan für MSFS 2020 & 2024:
  - Multi-Pfad-Verwaltung: scannt Community-, Official- und MSFS 2024 
    StreamedPackages-Verzeichnisse.
  - Benutzerdefinierte Pfade: beliebige Ordner hinzufügen, benennen und aktivieren oder deaktivieren.
  - Exakte Metadaten: auslesen von Layouts, Koordinaten, Start- und Landebahnen und Paketdaten.
  - Automatische GSX Pro Profilzuordnung: erkennt verknüpfte .ini-Profile 
    in %APPDATA%\Virtuali\GSX\MSFS.

* Finanz- und Sammlungs-Dashboard:
  - Gesamtausgaben-Übersicht: Live-Anzeige der kumulierten Gesamtausgaben aller Payware-Szenerien.
  - Multi-Währungssystem: umschalten zwischen USD ($), EUR (€), GBP (£) und AUD (A$); 
    alle Beträge in der Anwendung werden sofort umgerechnet.
  - Manueller Preisabgleich: überschreiben Sie bezahlte Preise für individuelle 
    Angebote oder Bundles in den Flughafendetails.
  - Länder-Investitionsansicht: detaillierte Länderanalyse mit Gesamtausgaben, 
    Anzahl der Flughäfen und Direktfokus auf der Karte.

* Live-Shop-Preisvergleich & Entwickler-Stores:
  - Multi-Shop-Aggregator: Echtzeit-Verfügbarkeits- und Preisprüfung bei über 15 Stores 
    (simMarket, Orbx Direct, Flightbeam Studios, iniBuilds Store, Aerosoft Shop, 
    France VFR, FlyTampa, FSDreamTeam, Jetstream Designs, LatinVFR, Pyreegue, 
    NZA Simulations, Drzewiecki Design, Contrail, Flightsim.to).
  - Günstigster Preis zuerst: automatische Sortierung aufsteigend nach dem besten 
    Preis in Ihrer gewählten Währung.
  - Hervorhebung offizieller Studios [OFFICIAL DEV]: goldene Abzeichen für direkte Entwickler-Websites.
  - Intelligenter Falsch-Positiv-Filter: schließt historische Retro-Szenerien (Genf 1935), 
    Stadt-Wahrzeichen (Paris Landmarks), Lackierungen, Profile und ältere Simulatoren 
    (FSX, P3D, X-Plane) zuverlässig aus.
  - Paralleles Stöbern: das Vergleichsfenster bleibt nach dem Klick geöffnet für 
    bequemes Vergleichen im Browser.

* Exporte & Datensicherung:
  - CSV-Export: kompatibel mit Excel, Google Tabellen, Volanta und Elevatex.
  - JSON-Komplettsicherung: vollständiger strukturierter Metadatenexport für Backups und Werkzeuge.

* Anzeige & Ergonomie:
  - Automatische Auflösungserkennung: automatische Größenanpassung auf 1080p-, 1440p (2K)- 
    und 4K-Monitoren.
  - Perfekt zentriert: exakt berechnete Ränder unter Berücksichtigung der Windows-Taskleiste.
  - 4 vollständige Sprachen: Deutsch, Englisch, Französisch und Spanisch.

================================================================================
4. DOCUMENTACIÓN EN ESPAÑOL
================================================================================

4.1 RESUMEN
SceneryX es una suite de escritorio moderna y de alto rendimiento diseñada 
específicamente para pilotos y aficionados de Microsoft Flight Simulator 
(MSFS 2020 y MSFS 2024). Integra en un único entorno la gestión de bibliotecas 
de escenarios, el control de inversión financiera en complementos y la comparación 
de precios en tiendas especializadas en tiempo real.

Distribuido como un archivo ejecutable único con una interfaz oscura estilo cabina 
en vidrio esmerilado (glassmorphism), SceneryX facilita la organización y auditoría 
de cientos de aeropuertos instalados.

4.2 CARACTERÍSTICAS PRINCIPALES

* Mapa Global Interactivo 3D/2D:
  - Integración Leaflet & MarkerCluster: visualización fluida de todos los aeropuertos 
    instalados con agrupación dinámica por regiones.
  - Control cinemático de cámara: movimientos suaves de desplazamiento y zoom con 
    velocidad configurable (Rápido, Suave, Cinemático) y profundidad de zoom 
    predeterminada (Amplio, Regional, Pista).
  - Región inicial configurable: seleccione su encuadre geográfico predeterminado 
    (Mundo, Europa Occidental, Norteamérica, Asia, Oceanía, etc.).
  - Vistas previas al pasar el cursor: consulte código OACI, ciudad, país, categoría 
    (Payware, Freeware, Asobo) y perfiles GSX activos.

* Escaneo Profundo Multi-Simulador (MSFS 2020 & 2024):
  - Gestor multi-directorio: escanea carpetas Community, Official y paquetes 
    transmitidos de MSFS 2024 (StreamedPackages).
  - Rutas personalizadas: añada, nombre y active o desactive carpetas según sus necesidades.
  - Metadatos precisos: extracción de pistas, coordenadas geográficas y datos de manifiesto.
  - Detección automática de perfiles GSX Pro: vincula automáticamente los perfiles .ini 
    ubicados en %APPDATA%\Virtuali\GSX\MSFS.

* Panel de Control Financiero y Colección:
  - Gasto total acumulado: indicador superior en tiempo real con la suma total 
    invertida en escenarios de pago.
  - Sistema multidivisa: cambie entre USD ($), EUR (€), GBP (£) y AUD (A$); todos 
    los importes y símbolos se recalculan de inmediato.
  - Precio personalizable: modifique el importe pagado por cada aeropuerto 
    (ofertas, paquetes) en la ficha técnica.
  - Desglose por país: consulta de inversión total, cantidad de aeropuertos y lista 
    interactiva con enfoque directo en el mapa.

* Comparador de Precios en Tiendas Oficiales:
  - Agregador de tiendas en vivo: consulta en tiempo real en más de 15 tiendas y 
    estudios oficiales (simMarket, Orbx Direct, Flightbeam Studios, iniBuilds Store, 
    Aerosoft Shop, France VFR, FlyTampa, FSDreamTeam, Jetstream Designs, LatinVFR, 
    Pyreegue, NZA Simulations, Drzewiecki Design, Contrail, Flightsim.to).
  - Orden ascendente (más barato primero): ordena automáticamente las tiendas 
    desde el precio más económico.
  - Reconocimiento de estudios oficiales [OFFICIAL DEV]: distintivo dorado para 
    tiendas oficiales de los desarrolladores.
  - Filtro inteligente anti-falsos positivos: bloquea paquetes retro (Ginebra 1935), 
    monumentos urbanos (Paris Landmarks), libreas, texturas, perfiles GSX y 
    simuladores anteriores (FSX, P3D, X-Plane).
  - Consulta continua: la ventana emergente no se cierra al abrir un enlace, 
    permitiendo contrastar varias ofertas simultáneamente.

* Exportación y Copias de Seguridad:
  - Hoja de cálculo CSV: exportación compatible con Excel, Google Sheets, Volanta y Elevatex.
  - Copia de seguridad JSON: exportación estructurada de metadatos completos para respaldo.

* Ergonomía y Visualización:
  - Detección automática de pantalla: adaptación a resoluciones 1080p, 1440p (2K) y 4K.
  - Centrado al píxel: márgenes calculados equilibrados teniendo en cuenta la barra 
    de tareas de Windows.
  - 4 idiomas completos: Español, Inglés, Francés y Alemán.

================================================================================
5. LEGAL MENTIONS & DISCLAIMERS / MENTIONS LÉGALES
================================================================================

5.1 GENERAL DISCLAIMER / CLAUSE DE NON-RESPONSABILITÉ
SceneryX is an independent, non-commercial software suite provided on an "AS IS" 
and "AS AVAILABLE" basis, without warranty of any kind, either express or implied, 
including but not limited to the implied warranties of merchantability, fitness 
for a particular purpose, or non-infringement.

The authors and copyright holders shall in no event be held liable for any claim, 
damages, data loss, file system corruption, simulator instability, or other liability 
arising from, out of, or in connection with the software or the use or other dealings 
in the software. Users interact with simulator configurations, Community packages, 
and Content.xml entirely at their own discretion and risk.

5.2 TRADEMARK NOTICES & NON-AFFILIATION
- Microsoft, Microsoft Flight Simulator, MSFS 2020, MSFS 2024, Windows, and the 
  Windows Logo are registered trademarks or trademarks of Microsoft Corporation 
  in the United States and/or other countries.
- Asobo Studio is a registered trademark of Asobo Studio SAS.
- Lockheed Martin and Prepar3D are registered trademarks of Lockheed Martin Corporation.
- Laminar Research and X-Plane are registered trademarks of Laminar Research.
- GSX Pro and FSDreamTeam are registered trademarks of VIRTUALI s.a.s.
- simMarket, Orbx, Aerosoft, iniBuilds, Flightbeam, FlyTampa, Flightsim.to, France VFR, 
  and other third-party vendor names and logos are trademarks of their respective owners.
- SceneryX is an independent community project and is NOT affiliated with, authorized, 
  sponsored, or endorsed by Microsoft Corporation, Asobo Studio, or any third-party 
  developer or storefront mentioned.

5.3 DATA PRIVACY & LOCAL PROCESSING
- 100% Local Processing: SceneryX does NOT collect, harvest, store, or transmit any 
  personal identifying information, simulator telemetry, credentials, or analytical data.
- External Web Queries: Network traffic generated by SceneryX is strictly restricted 
  to public search endpoints of flight simulation storefronts (to check add-on 
  availability and pricing).
- No user data is stored on remote servers; all settings and library databases 
  reside strictly on your local machine (%APPDATA%\SceneryX and application directory).

5.4 LICENSE & REDISTRIBUTION
SceneryX is distributed for free personal, non-commercial use. Modifying, 
reverse-engineering, decompiling, or redistributing the software for commercial 
gain without explicit prior written authorization from the copyright owner is prohibited.

--------------------------------------------------------------------------------
Developed with precision for the global flight simulation community.
================================================================================
