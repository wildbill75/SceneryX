const LOCALES = {
    en: {
        // Top Header Stats
        "stat.payware": "PAYWARE",
        "stat.freeware": "FREEWARE",
        "stat.asobo": "ASOBO",
        "stat.default": "DEFAULT MSFS",
        "stat.spent_prefix": "YOU HAVE SPENT",
        "stat.spent_suffix": "ON PAYWARE SCENERIES SO FAR !",
        "stat.tooltip_payware": "Click to filter Payware sceneries",
        "stat.tooltip_freeware": "Click to filter Freeware sceneries",
        "stat.tooltip_asobo": "Click to filter Asobo sceneries",
        "stat.tooltip_default": "Click to filter Default MSFS procedural airports",
        "header.support_title": "Support Project",

        // Sidebar Filters Headers & Tooltips
        "filter.pricing_model": "Pricing Model",
        "filter.pricing_tooltip": "Filter sceneries by pricing model: Payware, Freeware, Asobo handcrafted, or Default MSFS.",
        "filter.price_all": "All Models",
        "filter.price_all_tooltip": "Show all sceneries across all pricing categories",
        "filter.price_payware": "Payware",
        "filter.price_payware_tooltip": "Show only third-party commercial payware sceneries",
        "filter.price_freeware": "Freeware",
        "filter.price_freeware_tooltip": "Show community freeware sceneries (Flightsim.to, etc.)",
        "filter.price_asobo": "Asobo",
        "filter.price_asobo_tooltip": "Show official handcrafted sceneries bundled by Microsoft & Asobo",
        "filter.price_default": "Default MSFS",
        "filter.price_default_tooltip": "Show standard procedural default MSFS base airports",

        "filter.scenery_source": "Scenery Source",
        "filter.source_tooltip": "Filter sceneries by package origin: Community folders, Marketplace, or Official content.",
        "filter.src_all": "All Sources",
        "filter.src_all_tooltip": "Show all sceneries across all sources (Community, Marketplace, and Official)",
        "filter.src_community": "Community",
        "filter.src_community_tooltip": "Third-party sceneries and addons installed in Community folders or custom directories (+ Add Path, Addon Linker)",
        "filter.src_marketplace": "Marketplace",
        "filter.src_marketplace_tooltip": "Third-party sceneries purchased directly from Microsoft's in-game Marketplace (iniBuilds, Aerosoft, France VFR...)",
        "filter.src_official": "Official",
        "filter.src_official_tooltip": "Official Microsoft & Asobo handcrafted content (World Updates, City Updates, Deluxe editions)",

        "filter.geographic_region": "Geographic Region",
        "filter.region_tooltip": "Filter airports by continental zone and focus the camera on that region.",
        "filter.region_all": "All Regions",
        "filter.region_all_tooltip": "Show airports across all world regions",
        "filter.region_weurope": "Western Europe",
        "filter.region_weurope_tooltip": "Western Europe (France, UK, Germany, Spain, Italy...)",
        "filter.region_eeurope": "Eastern Europe",
        "filter.region_eeurope_tooltip": "Eastern Europe (Poland, Greece, Turkey, Romania...)",
        "filter.region_namerica": "North America",
        "filter.region_namerica_tooltip": "North America (United States, Canada, Greenland)",
        "filter.region_camerica": "Central America & Caribbean",
        "filter.region_camerica_tooltip": "Central America & Caribbean (Mexico, Panama, Bahamas...)",
        "filter.region_samerica": "South America",
        "filter.region_samerica_tooltip": "South America (Brazil, Argentina, Colombia, Chile...)",
        "filter.region_asia": "Asia",
        "filter.region_asia_tooltip": "Asia (Japan, China, India, Thailand, Indonesia...)",
        "filter.region_middleeast": "Middle East",
        "filter.region_middleeast_tooltip": "Middle East (UAE, Saudi Arabia, Qatar, Israel...)",
        "filter.region_nafrica": "North Africa",
        "filter.region_nafrica_tooltip": "North Africa (Egypt, Morocco, Algeria, Tunisia...)",
        "filter.region_ssafrica": "Sub-Saharan Africa",
        "filter.region_ssafrica_tooltip": "Sub-Saharan Africa (South Africa, Kenya, Nigeria...)",
        "filter.region_oceania": "Oceania",
        "filter.region_oceania_tooltip": "Oceania (Australia, New Zealand, Papua New Guinea)",
        "filter.region_pacific": "Pacific Ocean",
        "filter.region_pacific_tooltip": "Pacific Ocean islands & territories",

        "filter.airport_type": "Airport Type",
        "filter.type_tooltip": "Filter airports by classification: International, Regional, General Aviation, or Heli/Water.",
        "filter.type_all": "All Types",
        "filter.type_all_tooltip": "Show all airport types",
        "filter.type_international": "International",
        "filter.type_international_tooltip": "Major international hubs with commercial airline service",
        "filter.type_regional": "Regional",
        "filter.type_regional_tooltip": "Regional airports serving domestic or local commercial routes",
        "filter.type_ga": "General Aviation",
        "filter.type_ga_tooltip": "General aviation airfields for private, club, and sport flying",
        "filter.type_heli_water": "Heli / Water",
        "filter.type_heli_water_tooltip": "Heliports, helipads, and seaplane water runways",

        "filter.gsx_profile": "GSX Profile",
        "filter.gsx_tooltip": "Filter airports according to whether a custom GSX Pro ground handling profile (.ini) is installed.",
        "filter.gsx_all": "All",
        "filter.gsx_all_tooltip": "Show all airports with or without GSX profiles",
        "filter.gsx_with": "With",
        "filter.gsx_with_tooltip": "Show only airports with an active GSX profile installed",
        "filter.gsx_none": "No Profile",
        "filter.gsx_none_tooltip": "Show only airports without a GSX profile",

        "filter.user_rating": "Minimum User Rating",
        "filter.rating_tooltip": "Filter airports by your personal star rating to quickly highlight your favorite sceneries.",
        "filter.rating_widget_tooltip": "Click a star to set the minimum rating threshold (e.g. 4 stars to see 4★ and 5★ airports).",
        "filter.rating_reset": "Reset",
        "filter.rating_reset_tooltip": "Reset Rating Filter to 0.0★",

        // Sidebar Footer Actions
        "footer.search_placeholder": "Search ICAO, Airport, City or Country...",
        "footer.export_button": "Export Sceneries",
        "footer.rescan_button": "Rescan Packages",
        "footer.settings_tooltip": "Settings & Scenery Paths",

        // Rescan Modal
        "rescan.title_scanning": "Scanning Sceneries",
        "rescan.sub_checking": "Checking Community & OneStore folders...",
        "rescan.step_manifests": "Scanning package manifests & sceneries...",
        "rescan.step_bgl": "Analyzing runway & airport BGL files...",
        "rescan.step_indexing": "Indexing custom addons & GSX profiles...",
        "rescan.complete": "Scan Complete",
        "rescan.completed_title": "Scan Completed",
        "rescan.no_addon": "No new addon detected.",
        "rescan.new_packages_found": "new scenery package(s) detected and indexed:",
        "rescan.ok_button": "OK",

        // Settings Modal
        "settings.title": "Settings",
        "settings.auto_scan": "Auto Scan on Startup",
        "settings.scenery_paths": "Configured Scenery Paths",
        "settings.add_path": "Add Path",
        "settings.gsx_directory": "GSX Profile Directory (.ini)",
        "settings.browse": "Browse",
        "settings.camera_section": "Camera Settings",
        "settings.reset_default": "Reset to Default",
        "settings.save_camera": "Save Camera",
        "settings.saved_badge": "Saved",
        "settings.startup_region": "Default Startup Region",
        "settings.initial_viewport": "Initial viewport",
        "settings.airport_zoom": "Airport Selection Zoom",
        "settings.pan_duration": "Camera Pan Duration",
        "settings.zoom_wide": "Wide (4.0)",
        "settings.zoom_regional": "Regional (6.0)",
        "settings.zoom_runway": "Runway (12.0)",
        "settings.speed_fast": "Fast (0.2s)",
        "settings.speed_smooth": "Smooth (0.8s)",
        "settings.speed_cinematic": "Cinematic (2.0s)",
        "settings.language_section": "Language",
        "settings.language_label": "Application Language",
        "settings.reset_db": "Reset Database",
        "settings.cancel": "Cancel",
        "settings.save": "Save",

        // Modal Alerts & Dialogs
        "modal.file_read_error": "File Read Error",
        "modal.file_read_error_msg": "Unable to read the dropped file.",
        "modal.gsx_installed": "GSX Profile Installed",
        "modal.gsx_installed_msg": "GSX profile(s) successfully extracted and installed:",
        "modal.gsx_info": "GSX Profile Information",
        "modal.gsx_error": "GSX Installation Error",
        "modal.continue": "Continue",
        "modal.cancel": "Cancel",
        "modal.ok": "OK",
        "exit.simbrief_title": "Active SimBrief Flight Plan",
        "exit.simbrief_msg": "A SimBrief flight plan is currently active in SceneryX (off-route sceneries are isolated and disabled in MSFS to optimize performance).\n\nWhat would you like to do before exiting SceneryX?",
        "exit.keep_isolation": "Keep Isolation (In Flight)",
        "exit.restore_sceneries": "Restore All Sceneries"
    },

    fr: {
        // Top Header Stats
        "stat.payware": "PAYANT",
        "stat.freeware": "GRATUIT",
        "stat.asobo": "ASOBO",
        "stat.default": "PAR DÉFAUT MSFS",
        "stat.spent_prefix": "VOUS AVEZ DÉPENSÉ",
        "stat.spent_suffix": "EN SCÈNES PAYANTES JUSQU'ICI !",
        "stat.tooltip_payware": "Cliquer pour filtrer les scènes payantes",
        "stat.tooltip_freeware": "Cliquer pour filtrer les scènes gratuites",
        "stat.tooltip_asobo": "Cliquer pour filtrer les scènes Asobo",
        "stat.tooltip_default": "Cliquer pour filtrer les aéroports de base MSFS",
        "header.support_title": "Soutenir le projet",

        // Sidebar Filters Headers & Tooltips
        "filter.pricing_model": "Modèle Tarifaire",
        "filter.pricing_tooltip": "Filtrer les scènes par modèle tarifaire : Payant, Gratuit, Asobo ou par défaut MSFS.",
        "filter.price_all": "Tous les modèles",
        "filter.price_all_tooltip": "Afficher toutes les scènes de toutes catégories tarifaires",
        "filter.price_payware": "Payant",
        "filter.price_payware_tooltip": "Afficher uniquement les scènes commerciales tierces (Payware)",
        "filter.price_freeware": "Gratuit",
        "filter.price_freeware_tooltip": "Afficher les scènes communautaires gratuites (Flightsim.to, etc.)",
        "filter.price_asobo": "Asobo",
        "filter.price_asobo_tooltip": "Afficher les scènes officielles conçues par Microsoft & Asobo",
        "filter.price_default": "Par défaut MSFS",
        "filter.price_default_tooltip": "Afficher les aéroports génériques de base de MSFS",

        "filter.scenery_source": "Source de la Scène",
        "filter.source_tooltip": "Filtrer les scènes par origine du package : dossier Community, Marketplace ou contenu Officiel.",
        "filter.src_all": "Toutes les sources",
        "filter.src_all_tooltip": "Afficher toutes les scènes quelle que soit la source",
        "filter.src_community": "Community",
        "filter.src_community_tooltip": "Scènes tierces installées dans les dossiers Community ou répertoires personnalisés",
        "filter.src_marketplace": "Marketplace",
        "filter.src_marketplace_tooltip": "Scènes tierces achetées directement sur le Marketplace en jeu de Microsoft",
        "filter.src_official": "Officiel",
        "filter.src_official_tooltip": "Contenu officiel conçu par Microsoft & Asobo (World Updates, City Updates, Deluxe)",

        "filter.geographic_region": "Région Géographique",
        "filter.region_tooltip": "Filtrer les aéroports par continent et centrer la caméra sur cette région.",
        "filter.region_all": "Toutes les régions",
        "filter.region_all_tooltip": "Afficher les aéroports du monde entier",
        "filter.region_weurope": "Europe de l'Ouest",
        "filter.region_weurope_tooltip": "Europe de l'Ouest (France, Royaume-Uni, Allemagne, Espagne, Italie...)",
        "filter.region_eeurope": "Europe de l'Est",
        "filter.region_eeurope_tooltip": "Europe de l'Est (Pologne, Grèce, Turquie, Roumanie...)",
        "filter.region_namerica": "Amérique du Nord",
        "filter.region_namerica_tooltip": "Amérique du Nord (États-Unis, Canada, Groenland)",
        "filter.region_camerica": "Amérique Centrale & Caraïbes",
        "filter.region_camerica_tooltip": "Amérique Centrale & Caraïbes (Mexique, Panama, Bahamas...)",
        "filter.region_samerica": "Amérique du Sud",
        "filter.region_samerica_tooltip": "Amérique du Sud (Brésil, Argentine, Colombie, Chili...)",
        "filter.region_asia": "Asie",
        "filter.region_asia_tooltip": "Asie (Japon, Chine, Inde, Thaïlande, Indonésie...)",
        "filter.region_middleeast": "Moyen-Orient",
        "filter.region_middleeast_tooltip": "Moyen-Orient (Émirats, Arabie Saoudite, Qatar, Israël...)",
        "filter.region_nafrica": "Afrique du Nord",
        "filter.region_nafrica_tooltip": "Afrique du Nord (Égypte, Maroc, Algérie, Tunisie...)",
        "filter.region_ssafrica": "Afrique Subsaharienne",
        "filter.region_ssafrica_tooltip": "Afrique Subsaharienne (Afrique du Sud, Kenya, Nigeria...)",
        "filter.region_oceania": "Océanie",
        "filter.region_oceania_tooltip": "Océanie (Australie, Nouvelle-Zélande, Papouasie)",
        "filter.region_pacific": "Océan Pacifique",
        "filter.region_pacific_tooltip": "Îles et territoires de l'océan Pacifique",

        "filter.airport_type": "Type d'Aéroport",
        "filter.type_tooltip": "Filtrer les aéroports par catégorie : International, Régional, Aviation Générale ou Héliport/Hydrobase.",
        "filter.type_all": "Tous les types",
        "filter.type_all_tooltip": "Afficher tous les types d'aéroports",
        "filter.type_international": "International",
        "filter.type_international_tooltip": "Grands hubs internationaux avec liaisons aériennes commerciales",
        "filter.type_regional": "Régional",
        "filter.type_regional_tooltip": "Aéroports régionaux assurant des liaisons intérieures ou court-courrier",
        "filter.type_ga": "Aviation Générale",
        "filter.type_ga_tooltip": "Aérodromes d'aviation générale pour vols privés, aéroclubs et loisirs",
        "filter.type_heli_water": "Héliport / Hydrobase",
        "filter.type_heli_water_tooltip": "Héliports, hélistations et pistes hydrobases sur l'eau",

        "filter.gsx_profile": "Profil GSX",
        "filter.gsx_tooltip": "Filtrer les aéroports selon la présence d'un profil de services au sol GSX Pro (.ini).",
        "filter.gsx_all": "Tous",
        "filter.gsx_all_tooltip": "Afficher tous les aéroports avec ou sans profil GSX",
        "filter.gsx_with": "Avec",
        "filter.gsx_with_tooltip": "Afficher uniquement les aéroports avec un profil GSX actif installé",
        "filter.gsx_none": "Sans Profil",
        "filter.gsx_none_tooltip": "Afficher uniquement les aéroports sans profil GSX",

        "filter.user_rating": "Note Minimale Utilisateur",
        "filter.rating_tooltip": "Filtrer les aéroports par votre note personnelle (1 à 5 étoiles) pour mettre en valeur vos favoris.",
        "filter.rating_widget_tooltip": "Cliquer sur une étoile pour définir le seuil minimal (ex: 4 étoiles pour voir 4★ et 5★).",
        "filter.rating_reset": "Réinitialiser",
        "filter.rating_reset_tooltip": "Réinitialiser le filtre de note à 0.0★",

        // Sidebar Footer Actions
        "footer.search_placeholder": "Rechercher OACI, Aéroport, Ville ou Pays...",
        "footer.export_button": "Exporter les Scènes",
        "footer.rescan_button": "Rescanner les Packages",
        "footer.settings_tooltip": "Paramètres & Dossiers de Scènes",

        // Rescan Modal
        "rescan.title_scanning": "Analyse des Scènes",
        "rescan.sub_checking": "Vérification des dossiers Community & OneStore...",
        "rescan.step_manifests": "Analyse des manifestes de scènes...",
        "rescan.step_bgl": "Analyse des fichiers BGL de pistes et aéroports...",
        "rescan.step_indexing": "Indexation des scènes et profils GSX...",
        "rescan.complete": "Scan Terminé",
        "rescan.completed_title": "Scan Terminé",
        "rescan.no_addon": "Aucun nouvel addon détecté.",
        "rescan.new_packages_found": "nouveau(x) package(s) de scène détecté(s) :",
        "rescan.ok_button": "OK",

        // Settings Modal
        "settings.title": "Paramètres",
        "settings.auto_scan": "Scan automatique au démarrage",
        "settings.scenery_paths": "Dossiers de Scènes Configurés",
        "settings.add_path": "Ajouter un Dossier",
        "settings.gsx_directory": "Dossier des Profils GSX (.ini)",
        "settings.browse": "Parcourir",
        "settings.camera_section": "Paramètres Caméra",
        "settings.reset_default": "Rétablir par défaut",
        "settings.save_camera": "Sauvegarder Caméra",
        "settings.saved_badge": "Enregistré",
        "settings.startup_region": "Région de Démarrage par Défaut",
        "settings.initial_viewport": "Cadrage initial",
        "settings.airport_zoom": "Zoom à la Sélection d'un Aéroport",
        "settings.pan_duration": "Durée de Déplacement de la Caméra",
        "settings.zoom_wide": "Large (4.0)",
        "settings.zoom_regional": "Régional (6.0)",
        "settings.zoom_runway": "Piste (12.0)",
        "settings.speed_fast": "Rapide (0.2s)",
        "settings.speed_smooth": "Fluide (0.8s)",
        "settings.speed_cinematic": "Cinématique (2.0s)",
        "settings.language_section": "Langue",
        "settings.language_label": "Langue de l'application",
        "settings.reset_db": "Réinitialiser la Base",
        "settings.cancel": "Annuler",
        "settings.save": "Sauvegarder",

        // Modal Alerts & Dialogs
        "modal.file_read_error": "Erreur de Lecture",
        "modal.file_read_error_msg": "Impossible de lire le fichier déposé.",
        "modal.gsx_installed": "Profil GSX Installé",
        "modal.gsx_installed_msg": "Profil(s) GSX extrait(s) et installé(s) avec succès :",
        "modal.gsx_info": "Information Profil GSX",
        "modal.gsx_error": "Erreur d'Installation GSX",
        "modal.continue": "Continuer",
        "modal.cancel": "Annuler",
        "modal.ok": "OK",
        "exit.simbrief_title": "Plan de Vol SimBrief Actif",
        "exit.simbrief_msg": "Un plan de vol SimBrief est actuellement actif dans SceneryX (les scènes hors-route sont isolées et désactivées dans MSFS pour optimiser vos performances).\n\nQue souhaitez-vous faire avant de quitter SceneryX ?",
        "exit.keep_isolation": "Garder l'isolement (En Vol)",
        "exit.restore_sceneries": "Rétablir toutes mes scènes"
    },

    de: {
        // Top Header Stats
        "stat.payware": "PAYWARE",
        "stat.freeware": "FREEWARE",
        "stat.asobo": "ASOBO",
        "stat.default": "STANDARD MSFS",
        "stat.spent_prefix": "SIE HABEN BISHER",
        "stat.spent_suffix": "FÜR PAYWARE-SZENERIEN AUSGEGEBEN !",
        "stat.tooltip_payware": "Klicken, um Payware-Szenerien zu filtern",
        "stat.tooltip_freeware": "Klicken, um Freeware-Szenerien zu filtern",
        "stat.tooltip_asobo": "Klicken, um Asobo-Szenerien zu filtern",
        "stat.tooltip_default": "Klicken, um Standard-MSFS-Flughäfen zu filtern",
        "header.support_title": "Projekt unterstützen",

        // Sidebar Filters Headers & Tooltips
        "filter.pricing_model": "Preismodell",
        "filter.pricing_tooltip": "Szenerien nach Preismodell filtern: Payware, Freeware, Asobo oder Standard-MSFS.",
        "filter.price_all": "Alle Modelle",
        "filter.price_all_tooltip": "Alle Szenerien aller Preiskategorien anzeigen",
        "filter.price_payware": "Payware",
        "filter.price_payware_tooltip": "Nur kommerzielle Drittanbieter-Szenerien anzeigen",
        "filter.price_freeware": "Freeware",
        "filter.price_freeware_tooltip": "Kostenlose Community-Szenerien anzeigen (Flightsim.to usw.)",
        "filter.price_asobo": "Asobo",
        "filter.price_asobo_tooltip": "Offizielle von Microsoft & Asobo erstellte Szenerien anzeigen",
        "filter.price_default": "Standard MSFS",
        "filter.price_default_tooltip": "Standardmäßige prozedurale MSFS-Basisflughäfen anzeigen",

        "filter.scenery_source": "Szenerie-Quelle",
        "filter.source_tooltip": "Szenerien nach Paketursprung filtern: Community-Ordner, Marketplace oder offizieller Inhalt.",
        "filter.src_all": "Alle Quellen",
        "filter.src_all_tooltip": "Alle Szenerien aus allen Quellen anzeigen",
        "filter.src_community": "Community",
        "filter.src_community_tooltip": "Drittanbieter-Szenerien im Community-Ordner oder benutzerdefinierten Pfaden",
        "filter.src_marketplace": "Marketplace",
        "filter.src_marketplace_tooltip": "Direkt im Microsoft-In-Game-Marketplace gekaufte Szenerien",
        "filter.src_official": "Offiziell",
        "filter.src_official_tooltip": "Offizielle Inhalte von Microsoft & Asobo (World Updates, City Updates, Deluxe)",

        "filter.geographic_region": "Geografische Region",
        "filter.region_tooltip": "Flughäfen nach Kontinent filtern und die Kamera auf diese Region zentrieren.",
        "filter.region_all": "Alle Regionen",
        "filter.region_all_tooltip": "Flughäfen aller Weltregionen anzeigen",
        "filter.region_weurope": "Westeuropa",
        "filter.region_weurope_tooltip": "Westeuropa (Deutschland, Frankreich, Großbritannien, Spanien, Italien...)",
        "filter.region_eeurope": "Osteuropa",
        "filter.region_eeurope_tooltip": "Osteuropa (Polen, Griechenland, Türkei, Rumänien...)",
        "filter.region_namerica": "Nordamerika",
        "filter.region_namerica_tooltip": "Nordamerika (Vereinigte Staaten, Kanada, Grönland)",
        "filter.region_camerica": "Mittelamerika & Karibik",
        "filter.region_camerica_tooltip": "Mittelamerika & Karibik (Mexiko, Panama, Bahamas...)",
        "filter.region_samerica": "Südamerika",
        "filter.region_samerica_tooltip": "Südamerika (Brasilien, Argentinien, Kolumbien, Chile...)",
        "filter.region_asia": "Asien",
        "filter.region_asia_tooltip": "Asien (Japan, China, Indien, Thailand, Indonesien...)",
        "filter.region_middleeast": "Naher Osten",
        "filter.region_middleeast_tooltip": "Naher Osten (VAE, Saudi-Arabien, Katar, Israel...)",
        "filter.region_nafrica": "Nordafrika",
        "filter.region_nafrica_tooltip": "Nordafrika (Ägypten, Marokko, Algerien, Tunesien...)",
        "filter.region_ssafrica": "Subsahara-Afrika",
        "filter.region_ssafrica_tooltip": "Subsahara-Afrika (Südafrika, Kenia, Nigeria...)",
        "filter.region_oceania": "Ozeanien",
        "filter.region_oceania_tooltip": "Ozeanien (Australien, Neuseeland, Papua-Neuguinea)",
        "filter.region_pacific": "Pazifischer Ozean",
        "filter.region_pacific_tooltip": "Inseln und Territorien des Pazifischen Ozeans",

        "filter.airport_type": "Flughafentyp",
        "filter.type_tooltip": "Flughäfen nach Klassifizierung filtern: International, Regional, Allgemeine Luftfahrt oder Heli/Wasser.",
        "filter.type_all": "Alle Typen",
        "filter.type_all_tooltip": "Alle Flughafentypen anzeigen",
        "filter.type_international": "International",
        "filter.type_international_tooltip": "Große internationale Drehkreuze mit Linienflugverkehr",
        "filter.type_regional": "Regional",
        "filter.type_regional_tooltip": "Regionalflughäfen für Inlands- und Kurzstreckenflüge",
        "filter.type_ga": "Allgemeine Luftfahrt",
        "filter.type_ga_tooltip": "Flugplätze für Privat-, Vereins- und Sportfliegerei",
        "filter.type_heli_water": "Hubschrauber / Wasser",
        "filter.type_heli_water_tooltip": "Hubschrauberlandeplätze und Wasserflugzeug-Startbahnen",

        "filter.gsx_profile": "GSX-Profil",
        "filter.gsx_tooltip": "Flughäfen danach filtern, ob ein GSX Pro-Bodenabfertigungsprofil (.ini) installiert ist.",
        "filter.gsx_all": "Alle",
        "filter.gsx_all_tooltip": "Alle Flughäfen mit oder ohne GSX-Profile anzeigen",
        "filter.gsx_with": "Mit Profil",
        "filter.gsx_with_tooltip": "Nur Flughäfen mit aktivem GSX-Profil anzeigen",
        "filter.gsx_none": "Ohne Profil",
        "filter.gsx_none_tooltip": "Nur Flughäfen ohne GSX-Profil anzeigen",

        "filter.user_rating": "Mindestbewertung",
        "filter.rating_tooltip": "Flughäfen nach Ihrer persönlichen Sternebewertung filtern, um Favoriten hervorzuheben.",
        "filter.rating_widget_tooltip": "Auf einen Stern klicken, um den Mindestwert festzulegen (z. B. 4 Sterne für 4★ und 5★).",
        "filter.rating_reset": "Zurücksetzen",
        "filter.rating_reset_tooltip": "Bewertungsfilter auf 0.0★ zurücksetzen",

        // Sidebar Footer Actions
        "footer.search_placeholder": "ICAO, Flughafen, Stadt oder Land suchen...",
        "footer.export_button": "Szenerien exportieren",
        "footer.rescan_button": "Pakete neu scannen",
        "footer.settings_tooltip": "Einstellungen & Szeneriepfade",

        // Rescan Modal
        "rescan.title_scanning": "Szenerien scannen",
        "rescan.sub_checking": "Community- & OneStore-Ordner prüfen...",
        "rescan.step_manifests": "Paketmanifeste & Szenerien scannen...",
        "rescan.step_bgl": "Startbahn- & Flughafen-BGL-Dateien analysieren...",
        "rescan.step_indexing": "Addons & GSX-Profile indexieren...",
        "rescan.complete": "Scan abgeschlossen",
        "rescan.completed_title": "Scan abgeschlossen",
        "rescan.no_addon": "Kein neues Addon erkannt.",
        "rescan.new_packages_found": "neue(s) Szenerie-Paket(e) erkannt und indexiert:",
        "rescan.ok_button": "OK",

        // Settings Modal
        "settings.title": "Einstellungen",
        "settings.auto_scan": "Automatischer Scan beim Start",
        "settings.scenery_paths": "Konfigurierte Szeneriepfade",
        "settings.add_path": "Pfad hinzufügen",
        "settings.gsx_directory": "GSX-Profilverzeichnis (.ini)",
        "settings.browse": "Durchsuchen",
        "settings.camera_section": "Kamera-Einstellungen",
        "settings.reset_default": "Standard wiederherstellen",
        "settings.save_camera": "Kamera speichern",
        "settings.saved_badge": "Gespeichert",
        "settings.startup_region": "Standard-Startregion",
        "settings.initial_viewport": "Start-Blickfeld",
        "settings.airport_zoom": "Zoom bei Flughafenauswahl",
        "settings.pan_duration": "Kamera-Gleitdauer",
        "settings.zoom_wide": "Weit (4.0)",
        "settings.zoom_regional": "Regional (6.0)",
        "settings.zoom_runway": "Piste (12.0)",
        "settings.speed_fast": "Schnell (0.2s)",
        "settings.speed_smooth": "Sanft (0.8s)",
        "settings.speed_cinematic": "Kinematisch (2.0s)",
        "settings.language_section": "Sprache",
        "settings.language_label": "Anwendungssprache",
        "settings.reset_db": "Datenbank zurücksetzen",
        "settings.cancel": "Abbrechen",
        "settings.save": "Speichern",

        // Modal Alerts & Dialogs
        "modal.file_read_error": "Dateilesefehler",
        "modal.file_read_error_msg": "Die abgelegte Datei konnte nicht gelesen werden.",
        "modal.gsx_installed": "GSX-Profil installiert",
        "modal.gsx_installed_msg": "GSX-Profil(e) erfolgreich extrahiert und installiert:",
        "modal.gsx_info": "GSX-Profilinformation",
        "modal.gsx_error": "GSX-Installationsfehler",
        "modal.continue": "Weiter",
        "modal.cancel": "Abbrechen",
        "modal.ok": "OK",
        "exit.simbrief_title": "Aktiver SimBrief-Flugplan",
        "exit.simbrief_msg": "Ein SimBrief-Flugplan ist derzeit in SceneryX aktiv (Szenerien abseits der Route sind isoliert und in MSFS deaktiviert, um die Leistung zu optimieren).\n\nWas möchten Sie vor dem Beenden von SceneryX tun?",
        "exit.keep_isolation": "Isolation beibehalten (Im Flug)",
        "exit.restore_sceneries": "Alle Szenerien wiederherstellen"
    }
};

let currentLang = 'en';

function t(key, fallback = '') {
    if (typeof LOCALES !== 'undefined') {
        if (LOCALES[currentLang] && LOCALES[currentLang][key] !== undefined) {
            return LOCALES[currentLang][key];
        }
        if (LOCALES['en'] && LOCALES['en'][key] !== undefined) {
            return LOCALES['en'][key];
        }
    }
    return fallback || key;
}

function setAppLanguage(lang) {
    if (!LOCALES[lang]) lang = 'en';
    currentLang = lang;
    if (typeof currentSettings !== 'undefined' && currentSettings) {
        currentSettings.language = lang;
    }

    // Apply data-i18n to elements
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const k = el.getAttribute('data-i18n');
        if (k) el.innerText = t(k, el.innerText);
    });

    // Apply data-i18n-title to elements
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const k = el.getAttribute('data-i18n-title');
        if (k) el.setAttribute('title', t(k, el.getAttribute('title') || ''));
    });

    // Apply data-i18n-placeholder to inputs
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const k = el.getAttribute('data-i18n-placeholder');
        if (k) el.setAttribute('placeholder', t(k, el.getAttribute('placeholder') || ''));
    });

    // Update Language select if present in Settings modal
    const langSelect = document.getElementById('cfg-app-language');
    if (langSelect && langSelect.value !== lang) {
        langSelect.value = lang;
    }

    // Refresh dynamic stats banner if present
    if (typeof updateInvestmentBannerUI === 'function') {
        updateInvestmentBannerUI();
    }
}
