# 🚀 Zukunftsplan - Vinted Bot Roadmap

## 🎯 Feature in Planung: Multi-Channel Routing

**Status:** 🔸 Geplant  
**Kunde-Anfrage:** Verschiedene Suchbegriffe → verschiedene Discord-Channels

### Wie es funktionieren soll:
```
Nike      → Discord Channel 1
Adidas    → Discord Channel 2  
Puma      → Discord Channel 3
Sale      → Discord Channel 4
```

---

## 📋 Technische Umsetzung

### Schritt 1: New Config Entry
In `.env` hinzufügen:
```bash
# Multi-Channel Mapping (JSON Format)
CHANNEL_MAPPING='{"Nike": 123456789, "Adidas": 987654321, "Puma": 555666777}'
```

### Schritt 2: config.py erweitern
```python
import json

CHANNEL_MAPPING = json.loads(os.getenv("CHANNEL_MAPPING", "{}"))
```

### Schritt 3: data_discord.py anpassen
In der `sende_discord_nachricht()` Funktion:
```python
def get_channel_for_keyword(keyword):
    """Bestimmt Channel basierend auf Suchbegriff"""
    for mapped_keyword, channel_id in CHANNEL_MAPPING.items():
        if mapped_keyword.lower() in keyword.lower():
            return channel_id
    return CHANNELDISCORD  # Fallback zu Default-Channel
```

### Schritt 4: Command Update
Discord Command wird flexibler:
```
!start "Nike"     → Sendet zu Nike-Channel
!start "Adidas"   → Sendet zu Adidas-Channel
!start "Sonstiges" → Sendet zu Default-Channel
```

---

## ✅ Weitere Verbesserungen (Priorität)

### 🔴 High Priority
- [ ] **Multi-Channel Routing** (s.o.) - Feature für Kunde
- [ ] **Telegram Multi-Chat Support** - Parallel zu Discord
- [ ] **Suchfilter** (Größe, Preis, Zustand) per Channel
- [ ] **Admin-Panel** für Channel-Verwaltung ohne Code-Änderung

### 🟠 Medium Priority
- [ ] **Keyword-Blacklist** - Artikel die bestimmte Worte enthalten skippen
- [ ] **Preis-Benachrichtigungen** - Nur wenn unter X€
- [ ] **Duplikat-Detection über Bilder** - Gleiche Artikel mehrfach filtern
- [ ] **Bot-Status Dashboard** - Aktive Suchbegriffe, Statistiken
- [ ] **Auto-Retry bei Crash** - Besseres Error Recovery

### 🟡 Low Priority  
- [ ] **Automatische Tokenvalidation** - Token erneuerung via Bot
- [ ] **Database Backend** (statt JSON) - Mehr Skalierbarkeit
- [ ] **REST API** - Bot remotely bedienen
- [ ] **Web-UI** - Browser-Interface für Verwaltung

---

## 🔧 Interne Code-Verbesserungen

### Refactoring
- [ ] `data_telegram.py` + `data_discord.py` consolidieren (DRY-Prinzip)
- [ ] Retry-Logik in separate Modul auslagern (`retry.py`)
- [ ] Constants in separate `constants.py` datei
- [ ] Type Hints vollständig implementieren

### Testing
- [ ] Unit Tests für `artikel_suchen()`
- [ ] Integration Tests für Discord/Telegram
- [ ] Mock-Tests für API-Fehler-Szenarien

### Deployment
- [ ] GitHub Actions CI/CD Pipeline
- [ ] Automated Docker Image Builds
- [ ] Production Ready Checkliste

---

## 📅 Timeline Suggestion

| Phase | Features | Zeitraum |
|-------|----------|----------|
| **v1.1** | Multi-Channel Routing | 1 Woche |
| **v1.2** | Suchfilter (Preis, Größe) | 2 Wochen |
| **v1.3** | Admin-Panel / Web-UI | 3 Wochen |
| **v2.0** | Database Backend | Offen |

---

## 💾 Notes

- **Kunde-Fokus:** Multi-Channel Routing ist die nächste Priorität
- **Stabilität vor Features:** Fehlerfälle testen vor neuem Code
- **Docker-Ready:** Alle neuen Features müssen in Docker funktionieren
- **Dokumentation:** Alte Dateien aktualisieren wenn Code sich ändert

---

**Zuletzt aktualisiert:** 31. März 2026  
**Version:** 1.0 Roadmap
