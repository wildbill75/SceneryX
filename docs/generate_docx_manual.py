#!/usr/bin/env python3
"""
SceneryX - Word User Manual Generator
Generates SceneryX_User_Manual.docx with modern styling, clear sections,
and prominent screenshot placeholder callouts.
"""

import os
import sys
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUTPUT_DOCX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SceneryX_User_Manual.docx")

def set_cell_background(cell, hex_color):
    """Sets background shading of a table cell."""
    tcPr = cell._element.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=140, bottom=140, left=180, right=180):
    """Sets cell padding in dxa (1 pt = 20 dxa)."""
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)

def add_screenshot_box(doc, num, title, screen_name, elements_list, framing, description):
    """Adds a stylish callout box for pasting a screenshot."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)
    set_cell_background(cell, "F1F5F9")
    set_cell_margins(cell, top=160, bottom=160, left=200, right=200)

    # Header
    p_header = cell.paragraphs[0]
    p_header.paragraph_format.space_before = Pt(2)
    p_header.paragraph_format.space_after = Pt(4)
    run_icon = p_header.add_run(f"📸 CAPTURE D'ÉCRAN N°{num} : ")
    run_icon.bold = True
    run_icon.font.name = "Segoe UI"
    run_icon.font.size = Pt(10.5)
    run_icon.font.color.rgb = RGBColor(14, 116, 144) # Deep cyan / sky

    run_title = p_header.add_run(title)
    run_title.bold = True
    run_title.font.name = "Segoe UI"
    run_title.font.size = Pt(10.5)
    run_title.font.color.rgb = RGBColor(15, 23, 42) # Slate 900

    # Instructions
    p_details = cell.add_paragraph()
    p_details.paragraph_format.space_before = Pt(0)
    p_details.paragraph_format.space_after = Pt(6)
    p_details.paragraph_format.line_spacing = 1.15

    r1 = p_details.add_run("• Écran à afficher : ")
    r1.bold = True
    r1.font.size = Pt(9)
    r1.font.color.rgb = RGBColor(71, 85, 105)
    r1b = p_details.add_run(f"{screen_name}\n")
    r1b.font.size = Pt(9)
    r1b.font.color.rgb = RGBColor(15, 23, 42)

    r2 = p_details.add_run("• Éléments clés : ")
    r2.bold = True
    r2.font.size = Pt(9)
    r2.font.color.rgb = RGBColor(71, 85, 105)
    r2b = p_details.add_run(f"{elements_list}\n")
    r2b.font.size = Pt(9)
    r2b.font.color.rgb = RGBColor(15, 23, 42)

    r3 = p_details.add_run("• Cadrage conseillé : ")
    r3.bold = True
    r3.font.size = Pt(9)
    r3.font.color.rgb = RGBColor(71, 85, 105)
    r3b = p_details.add_run(f"{framing}")
    r3b.font.size = Pt(9)
    r3b.font.color.rgb = RGBColor(15, 23, 42)

    # Empty drop area / paste placeholder
    p_placeholder = cell.add_paragraph()
    p_placeholder.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_placeholder.paragraph_format.space_before = Pt(8)
    p_placeholder.paragraph_format.space_after = Pt(8)

    r_ph = p_placeholder.add_run("[ Collez votre capture d'écran ici (Ctrl + V) ]")
    r_ph.font.name = "Segoe UI"
    r_ph.font.size = Pt(9.5)
    r_ph.font.italic = True
    r_ph.font.color.rgb = RGBColor(148, 163, 184) # Muted slate

    # Caption / Legend
    p_leg = cell.add_paragraph()
    p_leg.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_leg.paragraph_format.space_before = Pt(2)
    p_leg.paragraph_format.space_after = Pt(2)
    r_leg = p_leg.add_run(f"Figure {num} — {description}")
    r_leg.font.name = "Segoe UI"
    r_leg.font.size = Pt(8.5)
    r_leg.font.italic = True
    r_leg.font.color.rgb = RGBColor(100, 116, 139)

    # Spacing after table
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(2)
    p_after.paragraph_format.space_after = Pt(6)

def generate_manual():
    doc = Document()

    # Page Margins (1 inch all around)
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

    # Header / Footer
    footer = sections[0].footer
    p_foot = footer.paragraphs[0]
    p_foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rf = p_foot.add_run("SceneryX RC_v1.0.5 — Manuel d'Utilisation Officiel • Sidestick Priority")
    rf.font.name = "Segoe UI"
    rf.font.size = Pt(8.5)
    rf.font.color.rgb = RGBColor(148, 163, 184)

    # =========================================================================
    # COVER / TITLE BLOCK
    # =========================================================================
    p_title_top = doc.add_paragraph()
    p_title_top.paragraph_format.space_before = Pt(24)
    p_title_top.paragraph_format.space_after = Pt(4)
    r_badge = p_title_top.add_run("SUITE LOGICIELLE OFFICIELLE • MICROSOFT FLIGHT SIMULATOR")
    r_badge.font.name = "Segoe UI"
    r_badge.font.size = Pt(9.5)
    r_badge.bold = True
    r_badge.font.color.rgb = RGBColor(2, 132, 199) # Sky blue

    p_main_title = doc.add_paragraph()
    p_main_title.paragraph_format.space_before = Pt(0)
    p_main_title.paragraph_format.space_after = Pt(6)
    r_title = p_main_title.add_run("SceneryX — Manuel d'Utilisation")
    r_title.font.name = "Segoe UI"
    r_title.font.size = Pt(24)
    r_title.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42) # Slate 900

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(18)
    r_sub = p_sub.add_run("Guide complet d'exploration, gestion des scènes, régulation Smart LOD et optimisation graphique.")
    r_sub.font.name = "Segoe UI"
    r_sub.font.size = Pt(11)
    r_sub.font.color.rgb = RGBColor(71, 85, 105)

    # Info bar table
    info_tbl = doc.add_table(rows=1, cols=3)
    info_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    info_tbl.autofit = False
    col_widths = [Inches(2.1), Inches(2.1), Inches(2.3)]
    for i, w in enumerate(col_widths):
        info_tbl.rows[0].cells[i].width = w
        set_cell_background(info_tbl.rows[0].cells[i], "0F172A")
        set_cell_margins(info_tbl.rows[0].cells[i], top=100, bottom=100, left=120, right=120)

    cells = info_tbl.rows[0].cells
    c0 = cells[0].paragraphs[0]
    r0 = c0.add_run("VERSION DU LOGICIEL\n")
    r0.font.size = Pt(7.5)
    r0.font.color.rgb = RGBColor(148, 163, 184)
    r0b = c0.add_run("Release Candidate v1.0.5")
    r0b.bold = True
    r0b.font.size = Pt(9.5)
    r0b.font.color.rgb = RGBColor(255, 255, 255)

    c1 = cells[1].paragraphs[0]
    r1 = c1.add_run("COMPATIBILITÉ SIMULATEUR\n")
    r1.font.size = Pt(7.5)
    r1.font.color.rgb = RGBColor(148, 163, 184)
    r1b = c1.add_run("MSFS 2020 & MSFS 2024")
    r1b.bold = True
    r1b.font.size = Pt(9.5)
    r1b.font.color.rgb = RGBColor(255, 255, 255)

    c2 = cells[2].paragraphs[0]
    r2 = c2.add_run("ÉDITEUR & ARCHITECTURE\n")
    r2.font.size = Pt(7.5)
    r2.font.color.rgb = RGBColor(148, 163, 184)
    r2b = c2.add_run("Sidestick Priority (x64 Native)")
    r2b.bold = True
    r2b.font.size = Pt(9.5)
    r2b.font.color.rgb = RGBColor(255, 255, 255)

    p_sep = doc.add_paragraph()
    p_sep.paragraph_format.space_before = Pt(16)
    p_sep.paragraph_format.space_after = Pt(12)

    # Helper function for Section Headings
    def add_section_h1(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(20)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.font.name = "Segoe UI"
        r.font.size = Pt(14)
        r.bold = True
        r.font.color.rgb = RGBColor(15, 23, 42)
        return p

    def add_section_h2(title):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(title)
        r.font.name = "Segoe UI"
        r.font.size = Pt(11.5)
        r.bold = True
        r.font.color.rgb = RGBColor(2, 132, 199)
        return p

    def add_body_p(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.line_spacing = 1.18
        r = p.add_run(text)
        r.font.name = "Segoe UI"
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(51, 65, 85)
        return p

    # =========================================================================
    # SECTION 1 : INTRODUCTION
    # =========================================================================
    add_section_h1("1. Introduction & Architecture Générale")
    add_body_p(
        "SceneryX est une application de bureau native 64 bits ultra-rapide conçue spécifiquement pour les pilotes virtuels sur Microsoft Flight Simulator. "
        "Elle réunit au sein d'un tableau de bord moderne et ergonomique la gestion complète des scènes installées, l'analyse télémétrique de vol, "
        "la régulation dynamique du niveau de détail (Smart LOD) et la calibration matérielle sur vos écrans haute fréquence et casques VR."
    )
    add_body_p(
        "Principes fondamentaux de SceneryX :\n"
        "• Préservation absolue de la stabilité : Vos fichiers originaux MSFS (UserCfg.opt) sont clonés de manière immaculée avant toute modification pour permettre un rollback instantané.\n"
        "• Détection multi-environnements : Prise en charge native et conjointe de MSFS 2020 (dossiers Community et Official) et MSFS 2024 (y compris les scènes streamées du cloud).\n"
        "• Synchronisation 1/2 Sync : Calibrage précis du nombre d'images par seconde sur la fréquence physique de votre moniteur pour éradiquer les micro-saccades."
    )

    # =========================================================================
    # SECTION 2 : INSTALLATION & LICENCE
    # =========================================================================
    add_section_h1("2. Installation, Clé de Licence & Premier Lancement")
    add_body_p(
        "L'installation s'opère via l'assistant SceneryX_Setup.exe. Si une version précédente de SceneryX est détectée, "
        "l'installeur applique une mise à jour directe sans réinitialiser vos chemins de scènes ni vos préférences personnalisées."
    )
    add_body_p(
        "À l'écran de validation de licence, saisissez votre clé de licence Lemon Squeezy (ou la clé permanente de test SCNX-MASTER-2026-OK). "
        "L'installeur audite votre configuration matérielle et initialise immédiatement deux profils standards équilibrés (2D Display Standard et VR Headset Standard) "
        "dans le dossier utilisateur %APPDATA%\\SceneryX\\custom_profiles\\."
    )

    add_screenshot_box(
        doc,
        num=1,
        title="Assistant d'Installation & Validation de Licence",
        screen_name="Assistant Windows Inno Setup (SceneryX Setup).",
        elements_list="Champ de saisie Lemon Squeezy avec la clé renseignée, boutons [Next >] et [Cancel].",
        framing="Fenêtre de l'assistant d'installation centrée (environ 700x500 px).",
        description="Écran d'activation de la licence produit lors de l'installation de SceneryX."
    )

    # =========================================================================
    # SECTION 3 : INTERFACE & NAVIGATION
    # =========================================================================
    add_section_h1("3. Interface Principale & Ergonomies de Navigation")
    add_body_p(
        "SceneryX vous offre le choix entre deux styles de navigation complémentaires, sélectionnables dans les Paramètres :"
    )
    add_section_h2("3.1 Mode Sidebar Classique (Flight Ops)")
    add_body_p(
        "La Sidebar latérale gauche regroupe l'arborescence des filtres, la sélection par pays, les détails financiers "
        "et la liste complète des aérodromes avec accès direct d'un clic."
    )
    add_section_h2("3.2 Mode Hub Radial Tactique")
    add_body_p(
        "Centré directement sur chaque terrain, le Hub Radial déploie 4 quadrants interactifs dédiés aux scènes installées, "
        "aux compagnies régulières, aux spécifications des pistes et au statut du profil GSX Pro."
    )

    add_screenshot_box(
        doc,
        num=2,
        title="Écran Principal — Vue Mappemonde Globale",
        screen_name="Fenêtre principale complète de SceneryX au démarrage.",
        elements_list="Carte Leaflet avec clusters d'aéroports par région, barre de stats supérieure (Payware, Freeware, Asobo, Investissement), barre d'outils inférieure.",
        framing="Plein écran 16:9 (1920x1080 ou 2560x1440).",
        description="Vue d'ensemble de la cartographie mondiale interactive et du statut global de votre bibliothèque."
    )

    add_screenshot_box(
        doc,
        num=3,
        title="Le Hub Radial Tactique en Action (ex. LPMA Madeira)",
        screen_name="Clic sur un aéroport en mode de navigation Radial.",
        elements_list="Anneau central ICAO avec les 4 quadrants interactifs déployés au-dessus de l'aérodrome sélectionné.",
        framing="Zoom centré sur le hub radial et l'aéroport (environ 900x700 px).",
        description="Menu contextuel circulaire permettant d'interroger instantanément l'ensemble des données d'un terrain."
    )

    # =========================================================================
    # SECTION 4 : FILTRES AVANCÉS
    # =========================================================================
    add_section_h1("4. Gestionnaire de Bibliothèque de Scènes & Filtres Avancés")
    add_body_p(
        "Le moteur de filtrage multicritère de la barre latérale permet d'isoler n'importe quel segment de votre collection :\n"
        "• Modèle économique : Payware, Freeware communautaire, créations artisanales Asobo (World Updates) ou terrains par défaut.\n"
        "• Source du package : Dossier Community local, packages officiels OneStore/Steam ou scènes streamées MSFS 2024.\n"
        "• Région géographique : Filtrage parmi 11 zones mondiales (Europe de l'Ouest, Amérique du Nord, Asie, etc.).\n"
        "• Catégorie de terrain : Grands hubs Internationaux, aéroports Régionaux, Aviation Générale (GA), Hydrobases ou Héliports.\n"
        "• Profil GSX : Repérage immédiat des terrains disposant d'un profil de sol ou nécessitant une configuration."
    )

    add_screenshot_box(
        doc,
        num=4,
        title="Panneau des Filtres Multicritères (Mode Classique)",
        screen_name="Sidebar gauche de SceneryX avec les catégories dépliées.",
        elements_list="Accordéons de filtres déployés avec des cases cochées et mise à jour dynamique des compteurs sur la carte.",
        framing="Colonne latérale gauche et bordure de carte (environ 450x900 px).",
        description="Filtres multicritères combinés permettant d'affiner l'affichage des aéroports selon vos préférences."
    )

    # =========================================================================
    # SECTION 5 : HUB AÉROPORT & CONFLITS
    # =========================================================================
    add_section_h1("5. Hub Aéroport, Gestion Multi-Scènes & Profils GSX Pro")
    add_body_p(
        "En cas de présence simultanée de plusieurs versions pour un même terrain (ex. une scène payware tierce et une scène officielle Asobo d'un World Update), "
        "SceneryX signale immédiatement le conflit potentiel. Vous pouvez basculer d'une version à l'autre via les interrupteurs individuels "
        "ou cliquer sur « Isoler » pour désactiver automatiquement les concurrentes et éliminer tout risque de collision visuelle."
    )
    add_body_p(
        "Scènes Complètes vs Correctifs Cumulables (Available Fixes) : Les scènes complètes d'un même aéroport (Payware, Freeware complet, Asobo / World Update, Aérodrome par défaut) "
        "s'excluent mutuellement (une seule active à la fois pour éviter les doublons géométriques). En revanche, les Available Fixes & Overlays "
        "(correctifs de taxiways, éclairage nocturne, retouches photogrammétriques, profils GSX Pro) sont totalement cumulables (stackables) "
        "avec des interrupteurs indépendants superposés à votre scène principale."
    )
    add_body_p(
        "Scènes Complètes vs Correctifs Cumulables (Available Fixes) : Les scènes complètes d'un même aéroport (Payware, Freeware complet, Asobo / World Update, Aérodrome par défaut) "
        "s'excluent mutuellement (une seule active à la fois pour éviter les doublons géométriques). En revanche, les Available Fixes & Overlays "
        "(correctifs de taxiways, éclairage nocturne, retouches photogrammétriques, profils GSX Pro) sont totalement cumulables (stackables) "
        "avec des interrupteurs indépendants superposés à votre scène principale."
    )
    add_body_p(
        "Pour GSX Pro, SceneryX analyse vos profils .ini et permet d'installer de nouveaux profils par simple glisser-déposer sur la carte."
    )

    add_screenshot_box(
        doc,
        num=5,
        title="Modale des Scènes Disponibles & Résolution de Conflits",
        screen_name="Fenêtre modale 'Available Add-ons' ouverte sur un aéroport multi-scènes.",
        elements_list="Liste des scènes concurrentes (Payware vs Asobo), interrupteurs de bascule, chemin d'accès et bouton d'isolation.",
        framing="Fenêtre modale centrée (environ 650x500 px).",
        description="Gestionnaire d'add-ons et résolution chirurgicale des doublons sans altération des fichiers."
    )

    # =========================================================================
    # SECTION 6 : COMPARATEUR DE PRIX
    # =========================================================================
    add_section_h1("6. Comparateur de Prix Payware en Direct (Store Comparator)")
    add_body_p(
        "Accessible depuis la fiche de chaque aéroport, le comparateur de prix interroge en temps réel plus de 15 boutiques en ligne "
        "(Orbx, simMarket, iniBuilds, Aerosoft, Flightbeam, Flightsim.to...). Les résultats sont classés par tarif croissant dans votre devise "
        "et identifient clairement les boutiques officielles de développeurs via le badge [OFFICIAL DEV]."
    )

    add_screenshot_box(
        doc,
        num=6,
        title="Comparateur de Prix Payware en Temps Réel",
        screen_name="Fenêtre 'Payware Scenery Search' sur une scène commerciale.",
        elements_list="Tableau comparatif des boutiques trié par prix croissant, badge doré [OFFICIAL DEV] et badge vert de l'offre la plus économique.",
        framing="Fenêtre modale du comparateur (environ 750x550 px).",
        description="Recherche tarifaire multi-boutiques en temps réel avec conversion de devises."
    )

    # =========================================================================
    # SECTION 7 : ROUTE & CORRIDOR SIMBRIEF
    # =========================================================================
    add_section_h1("7. Optimiseur de Route de Vol & Isolation SimBrief")
    add_body_p(
        "Ce module révolutionnaire résout les saturations de mémoire RAM et VRAM lors des vols long-courriers ou des arrivées sur gros aéroports. "
        "Importez votre plan de vol SimBrief actif, choisissez la largeur du corridor (ex. 60 NM) et cliquez sur « Isoler le Corridor » : "
        "toutes les scènes lourdes inutiles hors de votre trajectoire sont temporairement mises en sommeil, libérant plusieurs gigaoctets de mémoire pour votre simulateur."
    )

    add_screenshot_box(
        doc,
        num=7,
        title="Fenêtre d'Optimisation de Route & Corridor SimBrief",
        screen_name="Fenêtre flottante 'Flight Route Optimization' sur la carte du monde.",
        elements_list="Trace de vol reliant deux terrains (ex. LFPG ➔ LPMA), corridor bleuté sur la carte, calcul des Go libérés et bouton d'action.",
        framing="Vue d'ensemble montrant la fenêtre flottante et la trace du vol sur la carte (environ 1100x700 px).",
        description="Définition du corridor SimBrief et isolation temporaire des scènes hors trajectoire."
    )

    # =========================================================================
    # SECTION 8 : SMART LOD
    # =========================================================================
    add_section_h1("8. Régulateur Dynamique Smart LOD & Auto Cloud Recovery")
    add_body_p(
        "Le régulateur dynamique Smart LOD adapte la complexité d'affichage géométrique du monde (TLOD et OLOD) en fonction de l'altitude réelle de votre appareil :\n"
        "• Au sol / En approche : Valeur modérée pour décharger le processeur (MainThread) face à la densité des bâtiments et passerelles.\n"
        "• En transition : Montée progressive du niveau de détail.\n"
        "• En croisière : TLOD poussé à son maximum pour une visibilité cristalline sur les montagnes et côtes.\n"
        "• Auto Cloud Recovery : Réduction temporaire intelligente de la résolution des nuages en cas de vol dans des couches denses orageuses pour maintenir votre cadence cible sans saccade."
    )

    add_screenshot_box(
        doc,
        num=8,
        title="Panneau de Contrôle Smart LOD & Paliers d'Altitude",
        screen_name="Fenêtre flottante 'Smart LOD & Auto FPS'.",
        elements_list="Curseurs de réglage Ground, Transition et Cruise pour le TLOD/OLOD, interrupteur Auto Cloud Recovery et indicateur de cible FPS.",
        framing="Fenêtre flottante Smart LOD (environ 600x500 px).",
        description="Gouverneur dynamique de niveau de détail par palier d'altitude avec protection anti-saccades."
    )

    # =========================================================================
    # SECTION 9 : MY RIG & SYSTEM
    # =========================================================================
    add_section_h1("9. Diagnostic Matériel « MY RIG » & Optimiseur Système")
    add_body_p(
        "La fenêtre flottante MY RIG & SYSTEM propose un centre de contrôle à double volet rigoureusement différencié :\n"
        "SceneryX intègre un moteur de détection automatisé sondant les composants physiques de votre rig (cœurs/threads CPU, architecture et VRAM GPU, fréquence RAM & profil XMP/EXPO, débits NVMe, fréquence d'affichage et casques VR). Toutes les recommandations d'optimisation et profils du simulateur sont ainsi calculés sur-mesure d'après la baseline matérielle réelle de votre PC."
    )
    add_section_h2("9.1 System Optimizer (Optimisation Hors-Simulateur Windows & GPU)")
    add_body_p(
        "L'onglet System Optimizer arbore un bandeau d'état WINDOWS DIAGNOSIS avec pilule verte OPTIMAL justifiée à droite et audite 7 paramètres clés hors du simulateur :\n"
        "• GPU Scheduling (HAGS) : Planification GPU accélérée indispensable pour activer DLSS 3 Frame Generation et abaisser la latence. Modale GPU SCHEDULING (HAGS) épurée en anglais avec accès direct aux paramètres Windows 11 et commutateur UAC dans le registre (redémarrage PC requis).\n"
        "• DirectX Shader Cache : Mesure en temps réel de l'occupation sur disque en Mo vs quota alloué de 10 Go ou Illimité dans l'application GPU. Modale en anglais avec outil de purge sécurisé neutre sans jaune, accès NVIDIA App (avec menu complet) et Panneau NVIDIA classique (nvcpl.dll DCH).\n"
        "• Windows Game Mode : Priorité CPU accordée à MSFS et neutralisation des tâches d'arrière-plan via bascule directe.\n"
        "• Power Plan (Gestion d'Alimentation) : Commutation immédiate vers le mode Haute Performance ou Performances Ultimes.\n"
        "• Re-Size BAR : Vérification de l'adressage direct de la VRAM avec guide UEFI BIOS pas-à-pas.\n"
        "• GPU Driver & Control Panel : Détection de version face aux derniers pilotes WHQL et raccourcis de diagnostic.\n"
        "• Virtualization-Based Security (VBS / HVCI) : Détection de l'isolation du noyau Windows."
    )

    add_section_h2("9.2 Hardware Specs & Sélection d'Écran Haute Fréquence")
    add_body_p(
        "L'onglet Hardware Specs présente un bandeau supérieur RIG ARCHITECTURE avec pilule verte OPTIMAL justifiée à droite et infobulle d'évaluation globale :\n"
        "• Processeur (cœurs physiques, threads et architecture détectés).\n"
        "• Carte graphique (nom simplifié, mémoire VRAM dédiée et statut du pilote).\n"
        "• Mémoire RAM (capacité totale, fréquence en MHz et statut XMP / EXPO).\n"
        "• Stockage (SSD NVMe PCIe et espace libre sur le disque où résident vos scènes).\n"
        "• Détection multi-écrans & Cadence : Un seul clic sur un écran (ex. DISPLAY1 180 Hz ou DISPLAY2 165 Hz) sélectionne le moniteur de vol et met immédiatement à jour la cadence 1/2 Sync (90 FPS ou 82 FPS) dans votre UserCfg.opt sans redémarrage."
    )

    add_screenshot_box(
        doc,
        num=9,
        title="Fenêtre « MY RIG » (System Optimizer & Hardware Specs)",
        screen_name="Fenêtre flottante 'MY RIG & SYSTEM' avec ses onglets System Optimizer et Hardware Specs.",
        elements_list="Diagnostic Windows/GPU (HAGS, Game Mode, Shader Cache), bandeaux d'état avec pilules vertes OPTIMAL justifiées à droite, et sélecteur d'écrans haute fréquence.",
        framing="Fenêtre complète MY RIG (environ 700x520 px).",
        description="Optimisation de l'environnement Windows / GPU et diagnostic matériel en temps réel adapté aux spécifications du rig."
    )

    # =========================================================================
    # SECTION 10 : OPTIMISEUR GRAPHIQUE
    # =========================================================================
    add_section_h1("10. Optimiseur Graphique MSFS & Gestion du UserCfg.opt")
    add_body_p(
        "La matrice des paramètres graphiques traduit et ajuste l'ensemble des clés internes de votre simulateur selon trois modes étanches :\n"
        "• Mode Shared : Paramètres généraux (Résolution, Plein écran, V-Sync, Reflex).\n"
        "• Mode 2D Display : Calibré pour un affichage fluide sur écran plat (DLSS, Frame Generation 2X, limiteur 1/2 Sync).\n"
        "• Mode VR Headset : Profil haute performance dédié aux casques de réalité virtuelle, compatible OpenXR Toolkit (OFXR).\n"
        "Chaque paramètre bénéficie d'un badge clair (OPTIMUM, SWEET SPOT, ACCEPTABLE) vous guidant vers les meilleurs réglages sans tâtonnement."
    )

    add_screenshot_box(
        doc,
        num=10,
        title="Matrice des Paramètres Graphiques MSFS & Badges Sweet Spot",
        screen_name="Fenêtre 'MSFS Graphics Settings' sur l'onglet 2D Display.",
        elements_list="Lignes de paramètres Anti-Aliasing, Frame Generation, Max Frame Rate avec badge OPTIMUM, boutons 'Apply' et 'Rollback'.",
        framing="Tableau des paramètres graphiques (environ 850x600 px).",
        description="Configuration optimisée des paramètres graphiques MSFS avec recommandations et sécurité de restauration."
    )

    # =========================================================================
    # SECTION 11 : PANNEAU IN-GAME
    # =========================================================================
    add_section_h1("11. Panneau In-Game Cockpit (Toolbar HUD 2D & VR)")
    add_body_p(
        "Déployable directement dans le simulateur via le bouton « INSTALL » des Paramètres, le panneau in-game SceneryX "
        "fournit un affichage tête haute (HUD) semi-transparent dans le cockpit. Il permet d'ajuster les curseurs TLOD / OLOD à la volée "
        "et de surveiller la latence en millisecondes du MainThread CPU et la charge GPU en vol 2D comme en VR."
    )

    add_screenshot_box(
        doc,
        num=11,
        title="Le Panneau Toolbar SceneryX Actif dans le Cockpit MSFS",
        screen_name="Vue cockpit dans MSFS avec le panneau SceneryX ouvert depuis la barre d'outils.",
        elements_list="Widget HUD semi-transparent affichant les FPS, le temps de trame CPU en ms, les jauges TLOD/OLOD et l'Auto Cloud Recovery.",
        framing="Vue d'ensemble du cockpit avec le widget bien lisible (environ 1200x700 px).",
        description="Surveillance télémétrique et contrôle dynamique du Smart LOD directement depuis le cockpit en vol."
    )

    # =========================================================================
    # SECTION 12 : RAPPORTS DE VOL
    # =========================================================================
    add_section_h1("12. Enregistreur Télémétrique & Rapports de Performance")
    add_body_p(
        "Véritable boîte noire de votre simulateur, l'enregistreur de vol capture chaque seconde de vol. "
        "À l'arrivée, SceneryX génère un rapport graphique exhaustif : courbe de FPS réels, indicateur 1% Low, "
        "temps de trame CPU MainThread en millisecondes et détection précise des éventuelles micro-saccades."
    )

    add_screenshot_box(
        doc,
        num=12,
        title="Rapport Télémétrique de Vol & Graphiques de Fluidité",
        screen_name="Fenêtre 'Flight Performance Report' (Report Viewer).",
        elements_list="Graphique de fluidité interactive avec courbe de FPS, ligne 1% Low, barres de latence CPU MainThread et tableau de statistiques.",
        framing="Fenêtre de rapport complète (environ 900x650 px).",
        description="Rapport post-vol analysant la fluidité, les temps de réponse et la charge mémoire."
    )

    # =========================================================================
    # SECTION 13 : PARAMÈTRES GÉNÉRAUX
    # =========================================================================
    add_section_h1("13. Paramètres, Caméras & Préférences Générales")
    add_body_p(
        "Accessible via la roue dentée en bas à droite, la fenêtre des Paramètres regroupe :\n"
        "• Vos dossiers de scènes Community et Official.\n"
        "• Le chemin de vos profils GSX Pro.\n"
        "• Le bouton d'aide contextuelle '?' : Discret et sans bleu, il affiche un guide propre au menu sans relancer le tutoriel général.\n"
        "• Les réglages de caméra par défaut : Calibrés de manière optimale sur 8.0 (Zoom de sélection) et 1.1s (Durée de transition).\n"
        "• Le style d'interface (Sidebar Classique ou Hub Radial).\n"
        "• Le choix de la devise monétaire (EUR, USD, GBP, AUD) et de la langue d'interface."
    )

    add_screenshot_box(
        doc,
        num=13,
        title="Fenêtre des Paramètres & Préférences Générales",
        screen_name="Modale 'Folder Locations & Settings' ouverte.",
        elements_list="Chemins de packages, bouton d'aide '?', curseurs de caméra calés sur 8.0 et 1.1s, et sélecteurs de style/langue.",
        framing="Fenêtre des Paramètres centrée (environ 700x650 px).",
        description="Configuration générale de SceneryX avec valeurs de caméra optimisées et bouton d'aide dédié."
    )

    # Summary table of all 13 screenshots
    add_section_h1("Tableau Récapitulatif des 13 Captures d'Écran")
    add_body_p("Ce tableau vous permet de vérifier d'un coup d'œil que l'ensemble des 13 captures ont bien été intégrées dans votre manuel :")

    sum_tbl = doc.add_table(rows=1, cols=3)
    sum_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    sum_tbl.autofit = False
    sum_widths = [Inches(0.8), Inches(2.8), Inches(2.9)]
    for i, w in enumerate(sum_widths):
        sum_tbl.rows[0].cells[i].width = w
        set_cell_background(sum_tbl.rows[0].cells[i], "0F172A")
        set_cell_margins(sum_tbl.rows[0].cells[i], top=80, bottom=80, left=100, right=100)

    hdr = sum_tbl.rows[0].cells
    for i, h_text in enumerate(["N°", "TITRE DU VISUEL", "EMPLACEMENT"]):
        p = hdr[i].paragraphs[0]
        r = p.add_run(h_text)
        r.font.name = "Segoe UI"
        r.font.size = Pt(8.5)
        r.bold = True
        r.font.color.rgb = RGBColor(255, 255, 255)

    data = [
        ("01", "Assistant d'Installation & Clé Lemon Squeezy", "Installeur Setup.exe"),
        ("02", "Mappemonde Globale & Statut de Collection", "Écran principal SceneryX"),
        ("03", "Menu Hub Radial Tactique (ex. LPMA)", "Clic aéroport mode Radial"),
        ("04", "Panneau de Filtres Multicritères", "Sidebar gauche Classique"),
        ("05", "Gestionnaire d'Add-ons & Conflits Multi-Scènes", "Modale des scènes d'un terrain"),
        ("06", "Comparateur de Prix Payware en Direct", "Modale Payware Scenery Search"),
        ("07", "Tracé de Corridor SimBrief & Isolation", "Fenêtre Flight Route Optimization"),
        ("08", "Régulateur Dynamique Smart LOD", "Fenêtre Smart LOD & Auto FPS"),
        ("09", "Audit Matériel MY RIG & Sélecteur d'Écran", "Carte MY RIG HARDWARE"),
        ("10", "Matrice des Réglages Graphiques MSFS", "Fenêtre MSFS Graphics Settings"),
        ("11", "Panneau Toolbar HUD Cockpit MSFS", "Cockpit en vol MSFS"),
        ("12", "Rapport Télémétrique de Vol (Blackbox)", "Fenêtre Report Viewer"),
        ("13", "Fenêtre Paramètres & Caméras (8.0 / 1.1s)", "Modale des Paramètres")
    ]

    for row_idx, (n, t_name, loc) in enumerate(data):
        row = sum_tbl.add_row()
        bg_col = "F8FAFC" if row_idx % 2 == 0 else "FFFFFF"
        for i, w in enumerate(sum_widths):
            row.cells[i].width = w
            set_cell_background(row.cells[i], bg_col)
            set_cell_margins(row.cells[i], top=60, bottom=60, left=80, right=80)
        
        c0 = row.cells[0].paragraphs[0]
        r0 = c0.add_run(n)
        r0.font.name = "Segoe UI"
        r0.font.size = Pt(8.5)
        r0.bold = True
        r0.font.color.rgb = RGBColor(2, 132, 199)

        c1 = row.cells[1].paragraphs[0]
        r1 = c1.add_run(t_name)
        r1.font.name = "Segoe UI"
        r1.font.size = Pt(8.5)
        r1.font.color.rgb = RGBColor(15, 23, 42)

        c2 = row.cells[2].paragraphs[0]
        r2 = c2.add_run(loc)
        r2.font.name = "Segoe UI"
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = RGBColor(71, 85, 105)

    doc.save(OUTPUT_DOCX)
    print(f"[OK] Generated Word User Manual: {OUTPUT_DOCX} ({os.path.getsize(OUTPUT_DOCX)} bytes)")

if __name__ == "__main__":
    generate_manual()
