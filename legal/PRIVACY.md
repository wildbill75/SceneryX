# SCENERYX PRIVACY POLICY & LOCAL DATA COMMITMENT

**Last Updated: October 2026**  
**Publisher:** Sidestick Priority  
**Software:** SceneryX (Desktop Application for Microsoft Windows)

At **Sidestick Priority**, we believe that flight simulation should be an immersive and distraction-free experience. As flight sim enthusiasts ourselves, we respect the privacy of the flight simulation community and uphold a strict **Local-First, Zero-Surveillance** architecture.

This Privacy Policy explains how SceneryX handles data on your machine and outlines our technical commitments to your personal privacy.

---

### 1. ZERO PERSONAL DATA COLLECTION

1.1. **No Data Harvesting:** SceneryX does **not** collect, scrape, harvest, store, or sell any personal data, personally identifiable information (PII), biometric data, or private user credentials.

1.2. **No Hardware Fingerprinting:** SceneryX does not generate or transmit hardware fingerprints, unique device telemetry identifiers, or Windows registry user profiles to any central tracking server.

1.3. **No Behavioral Tracking:** SceneryX contains zero telemetry trackers, zero tracking pixels, zero analytics SDKs (such as Google Analytics or Mixpanel), and zero third-party advertising frameworks. Your flying habits, favorite airports, and scenery purchase histories remain exclusively on your computer.

---

### 2. LOCAL DATA STORAGE ARCHITECTURE

All configuration settings, catalog indexes, pricing overrides, and performance benchmarks used by SceneryX are generated locally and stored **strictly on your computer's local storage**:

2.1. **Local Files & Storage Paths:**
- `%APPDATA%\SceneryX\settings.json`: Stores your user interface preferences, currency choice, startup map coordinates, and camera speeds.
- `%APPDATA%\SceneryX\installed_airports.json`: The local indexing catalog of sceneries detected in your Community, Marketplace, and Linker folders.
- `%APPDATA%\SceneryX\ratings.json`: Your personal star ratings (1 to 5 stars) assigned to sceneries.
- `%APPDATA%\SceneryX\custom_prices.json`: Any custom purchase price overrides you enter for your sceneries.
- `%APPDATA%\SceneryX\library_snapshot.json`: Local cryptographic hashes and manifests used exclusively for fast startup delta detection.
- `%APPDATA%\SceneryX\custom_profiles\`: Locally saved graphics and Smart LOD tuning presets.

2.2. **Zero Cloud Sync:** None of these files are ever synced to cloud storage, remote databases, or external analytics endpoints. You maintain full and exclusive ownership over your local data.

---

### 3. THIRD-PARTY APIS & EXTERNAL SERVICES

SceneryX integrates with selected third-party flight simulation services strictly when initiated by user actions. Here is how data is handled with each service:

3.1. **SimBrief (Navigraph):**
- **Purpose:** When you choose to import an active flight plan or corridor, SceneryX queries SimBrief's public API to retrieve your latest Operational Flight Plan (OFP).
- **Data Used:** Only your public SimBrief **Pilot ID** or **Username** is used to request the active route.
- **Security:** SceneryX **never** asks for, receives, or stores your Navigraph or SimBrief password. All requests are made via standard encrypted HTTPS.

3.2. **Lemon Squeezy (License & Activation):**
- **Purpose:** If you purchase a license for SceneryX, your license key is validated upon first activation through Lemon Squeezy's secure licensing API.
- **Security:** Communications occur directly over encrypted HTTPS (`api.lemonsqueezy.com`). SceneryX **never** touches, receives, processes, or stores your credit card numbers, PayPal credentials, or billing address. All payment processing is handled exclusively by Lemon Squeezy acting as Merchant of Record.

3.3. **Store Lookups & Scenery Searches (Flightsim.to, Orbx, Contrail, SimMarket):**
- **Purpose:** When you click to check for scenery updates or explore catalog listings, SceneryX constructs a search query URL.
- **Execution:** All web searches open directly inside your computer's default web browser or execute public API requests without transmitting any personal identifiers or tracking telemetry.

---

### 4. DATA SECURITY & LOCAL PERMISSIONS

4.1. **Local File System Access:** SceneryX requires local file read/write access solely to scan packages in your MSFS Community and Official folders and safely stage temporary `Content.xml` configurations. It never reads or accesses personal files outside of flight simulator packages.

4.2. **Optional Crash Reports:** If an unhandled exception or crash occurs, SceneryX provides a diagnostic assistant. Crash logs contain only technical software traces and memory states strictly necessary for debugging; they are never submitted automatically without your explicit manual review and consent.

---

### 5. USER RIGHTS & COMPLETE DATA DELETION

You hold absolute control over all data managed by SceneryX:

5.1. **In-App Reset:** You can reset your entire local scenery database at any time using the "Reset Database" option in the Settings panel.

5.2. **Manual Deletion:** To completely erase all SceneryX data, simply delete the folder:  
`%APPDATA%\SceneryX\`  
This immediately and permanently removes all settings, indexes, ratings, and snapshots from your machine.

---

### 6. CONTACT & TRANSPARENCY

For questions regarding our privacy commitments or technical architecture, you can contact:

**Sidestick Priority**  
Official Project Repository: `https://github.com/wildbill75/SceneryX`
