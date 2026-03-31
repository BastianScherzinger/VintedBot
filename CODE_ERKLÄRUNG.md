# 📚 Code Erklärung - Vinted Bot

## 🎯 Alles Wichtige in 5 Minuten

---

## 📁 Dateistamm

```
VintedSCRAPER/
├── main.py              (Startet Discord + Telegram Bot)
├── config.py            (Lädt Token aus .env)
├── data_telegram.py     (Telegram Scraper)
├── data_discord.py      (Discord Scraper)
├── Dockerfile           (Docker Image)
├── compose.yaml         (Docker Start)
├── requirements.txt     (Python Pakete)
├── .env                 (Deine Tokens - GEHEIM!)
├── seen.json            (Artikel die schon gesendet wurden)
└── log.json             (Suchlogs)
```

---

## 🤖 Wie es funktioniert

### **Start-Prozess**
```
main.py startet
  → Liest .env (Tokens)
  → Startet Telegram Bot (läuft kontinuierlich)
  → Startet Discord Bot (wartet auf !start Befehle)
```

### **Telegram Bot**
- Sucht alle 30 Sekunden nach neuen Artikeln
- Sendet neue Artikel zu Telegram
- Merkt sich bereits sesendete (seen.json)

### **Discord Bot**
- Aktiviert via `!start "Suchbegriff"`
- Läuft als separater Prozess im Hintergrund
- Sendet zu Discord Channel statt Telegram

---

## ⚙️ Technisches

### **Retry-Logik**
Bei Fehler: 5 Versuche mit exponentiellem Backoff
```
Versuch 1 → 5s, Versuch 2 → 10s, 3 → 20s, 4 → 40s, 5 → 80s
```

### **Anti-Bot Schutz**
- Cookies alle 10 Min erneuert
- User-Agent wechselt (Chrome/Firefox/Edge)
- Session nach 50 Artikel-Requests erneuert

### **Deduplizierung**
Von jeden Artikel wird die ID in seen.json gespeichert
→ Keine Duplikate senden

---

## 🐳 Docker Setup

### **Dockerfile**
- Basis: Python 3.11
- Kopiert Code + .env
- Startet main.py

### **compose.yaml**
- Baut & startet Container
- Lädt .env (Tokens verfügbar)
- Auto-Restart bei Crash
- Speichert Daten persistent

**Resultat:** Kein Artikel wird zweimal gesendet!

---

## 📊 Dateien bei Laufzeit

### **seen.json** - Bereits gesehene Artikel
```json
[12345, 12346, 12347]
```
→ Speichert Artikel-IDs damit Bot nicht doppelt sendet

### **log.json** - Suchlogs
```json
[
  {"zeit": "2026-03-31 10:00:00", "suchbegriff": "Adidas Rot"},
  {"zeit": "2026-03-31 10:30:00", "suchbegriff": "Nike Schuhe"}
]
```
→ Für Audit/Nachverfolgung

---

## 🔑 Environment Variablen (.env)

```
TELEGRAM_TOKEN=...            # Token von @BotFather
TELEGRAM_CHAT_ID=...          # Deine Telegram Chat ID
DISCORD_TOKEN=...             # Token aus Discord Developer Portal
DISCORD_CHANNEL_ID=...        # Channel ID von Discord
SUCHBEGRIFF=sneaker           # Suchbegriff beim Start
```

**So werden sie geladen:**
```python
# config.py
from dotenv import load_dotenv
load_dotenv()  # Lädt .env
TOKEN = os.getenv("TELEGRAM_TOKEN")  # Holt Token
```

---

## 🔐 Sicherheit

✅ **Token-Management:**
- `.env` in `.gitignore` (nicht zu GitHub)
- `.env` wird NUR als Datei kopiert (`COPY .env .` in Dockerfile)
- Tokens nicht im Code hart-codiert

✅ **Keine Logs mit Tokens:**
- Bot gibt Tokens NICHT in Print/Logs aus

✅ **Session-Erneuerung:**
- Wechselt regelmäßig User-Agent
- Erneuert Cookies
- Verhindert Bot-Detection

---

## ⚡ Cheat Sheet

| Was | Code | Effekt |
|-----|------|--------|
| Lade .env | `load_dotenv()` | Macht Tokens verfügbar |
| Hol Token | `os.getenv("KEY")` | Gibt Token Value |
| Suche Artikel | `session.get(url, params)` | API Request zu Vinted |
| Sende Telegram | `requests.post(telegram_api)` | Nachricht → Telegram |
| Nach Fehler warten | `time.sleep(warte_zeit)` | Exponential Backoff |
| Speichere Artikel | `json.dump(seen_ids)` | Schreib seen.json |

---

## 🎯 Zusammenfassung

```
Docker Build:
  Dockerfile läuft
  → installiert Python
  → kopiert .env (Tokens!)
  → kopiert Code
  → erstellt Image

Docker Start:
  compose.yaml läuft
  → startet Image als Container
  → .env wird geladen
  → main.py startet
  → Telegram Bot + Discord Bot parallel
  → Beide suchen kontinuierlich nach Artikeln
  → Finden neue → senden sofort
  → Retry-Logic bei Fehler
  → Speichern als "gesehen"
  → Repeat
```

**Resultat:** 24/7 automatischer Bot, der Artikel findet! 🚀

---

**Fragen?** → Schreib oder öffne `START.html`