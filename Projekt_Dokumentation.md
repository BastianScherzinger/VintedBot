# 📄 Projekt-Dokumentation: Vinted Scraper v2.0 (Cloud-Edition)

Dieses Projekt ist ein hochoptimierter Vinted Scraper, der speziell für Performance, Stabilität und Cloud-Hosting (Render/Docker) entwickelt wurde.

---

## 🚀 Kern-Features & Stärken

### 1. Asynchroner Hochleistungs-Kern
Im Gegensatz zu herkömmlichen Scrapern nutzt dieser Bot `asyncio` und `Tasks`. Er kann dutzende Suchen gleichzeitig verarbeiten, ohne den Prozessor zu belasten oder den RAM zu sprengen.

### 2. Cloud-Native Architektur (Stateless)
Der Bot benötigt keine lokale Festplatte. Alle Daten (gesehene Artikel, Sucheinstellungen) werden in einer **MongoDB Atlas Cloud-Datenbank** gespeichert. Dies ermöglicht den Betrieb auf Plattformen wie Render.com Free Tier, wo Festplattendaten bei jedem Neustart gelöscht werden.

### 3. Effizientes HTML-Parsing (No-Browser)
Wir haben den RAM-hungrigen Chromium-Browser (Playwright) entfernt. Der Bot parst das HTML direkt via `requests`. 
- **Vorteil:** RAM-Verbrauch sank von 1.5GB auf unter 200MB!
- **Anti-Ban:** Durch intelligentes Header-Management und Proxy-Rotation bleibt der Bot unentdeckt.

### 4. Dynamisches Channel-Management
Per Discord-Befehl (`!new`) erstellt der Bot automatisch neue Kanäle und ordnet sie Kategorien zu. Er verteilt die Last automatisch auf verschiedene Hintergrund-Prozesse.

---

## 💎 Die Kommende PREMIUM VERSION

Die Premium-Version wird den Bot auf das Level eines professionellen Reselling-Tools heben:

### 🎭 Premium Proxy-Integration
- Unterstützung für **Residential Proxies** (Hausanschluss-IPs), die von Vinted praktisch nicht blockiert werden können.
- Automatischer Wechsel bei Fehlern innerhalb von Millisekunden.

### ⚡ Ultra-Fast Modus
- Noch schnellere Scan-Intervalle durch optimiertes Request-Pooling.
- Priorisierte Benachrichtigungen (unter 1 Sekunde Verzögerung).

### 📊 Admin-Dashboard
- Ein Web-Interface zur Verwaltung aller Suchen, Statistiken und Proxy-Health.

### 🛠️ Auto-Filter & KI-Check
- Automatisches Filtern von Scam-Angeboten durch KI-Analyse der Verkäuferprofile.
- Benachrichtigung nur bei "Top-Deals" mit hoher Marge.
