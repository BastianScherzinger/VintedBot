# 🚀 Vinted Scraper Bot

Ein automatischer Vinted-Scraper der neue Artikel in Echtzeit findet und per **Discord** und **Telegram** benachrichtigt.

> Made by **python_tutorials_de** 🎓

---

## ✨ Features

- 🔍 **Echtzeit-Suche** – Neue Artikel werden automatisch gefunden
- 📸 **Produktfotos** – Bilder werden mitgesendet
- 💶 **Preisanzeige** – Preis in EUR direkt sichtbar
- 🌍 **32 Länder** – Sucht in allen europäischen Vinted-Märkten
- 🗺️ **Standort-Erkennung** – Stadt & Land des Verkäufers via API + Playwright-Fallback
- 📊 **Live-Dashboard** – Visuelle Statistiken im Browser
- 🐳 **Docker-Ready** – Ein Befehl zum Starten

---

## ⚡ Schnellstart

### Voraussetzungen

- [Python 3.11+](https://www.python.org/downloads/) oder [Docker](https://www.docker.com/products/docker-desktop)
- Telegram Bot Token ([BotFather](https://t.me/BotFather))
- Discord Bot Token ([Developer Portal](https://discord.com/developers/applications))

### 1. Repository klonen

```bash
git clone https://github.com/DEIN_USERNAME/VintedSCRAPER.git
cd VintedSCRAPER
```

### 2. .env Datei erstellen

```bash
cp .env.example .env
```

Öffne `.env` und fülle deine Tokens ein:

```env
TELEGRAM_TOKEN=123456789:XXXXXXXXXXXXXXXXXXX
TELEGRAM_CHAT_ID=987654321
DISCORD_TOKEN=dzA1adfgd.XXXXXXXXXXXXXXXXXXXX
DISCORD_CHANNEL_ID=123456789012345678
```

### 3a. Mit Docker starten (empfohlen)

```bash
docker compose up -d
```

### 3b. Ohne Docker starten

```bash
pip install -r requirements.txt
playwright install chromium
python main.py
```

---

## 🐳 Docker

| Befehl | Beschreibung |
|--------|-------------|
| `docker compose up -d` | Bot im Hintergrund starten |
| `docker compose logs -f` | Live-Logs anzeigen |
| `docker compose down` | Bot stoppen |
| `docker compose up -d --build` | Neu bauen & starten |

---

## 📋 Bot-Befehle

### Discord

| Befehl | Beschreibung |
|--------|-------------|
| `!id` | Deine Discord ID anzeigen |
| `!new [Begriff]` | Neuer Kanal + Scraper starten |
| `!start [Begriff]` | Scraper im aktuellen Channel starten |
| `!suche [Begriff]` | Einmalige Schnellsuche |
| `!stop [Begriff]` | Scraper stoppen |
| `!delete [Begriff]` | Kanal löschen + Scraper stoppen |
| `!channels` | Alle aktiven Kanäle anzeigen |
| `!info` | Hilfe anzeigen |

### Telegram

| Befehl | Beschreibung |
|--------|-------------|
| `/id` | Deine Chat ID anzeigen |
| `/start [Begriff]` | Kontinuierliche Suche starten |
| `/suche [Begriff]` | Einmalige Schnellsuche |
| `/stop` | Scraper stoppen |
| `/info` | Hilfe anzeigen |

---

## 📁 Projektstruktur

```
VintedSCRAPER/
├── main.py              # Hauptdatei – startet Discord + Telegram Bot
├── data_discord.py      # Discord Scraper (Hintergrund-Prozess)
├── data_telegram.py     # Telegram Scraper (Hintergrund-Prozess)
├── get_adr.py           # Standort-Extraktion (API + Playwright)
├── config.py            # Telegram Token/Chat-ID Verwaltung
├── dashboard.py         # Live-Dashboard im Browser
├── .env.example         # Beispiel für .env Datei
├── requirements.txt     # Python-Abhängigkeiten
├── Dockerfile           # Docker Image Definition
├── compose.yaml         # Docker Compose Konfiguration
└── README.md            # Diese Datei
```

---

## 🌍 Unterstützte Länder

Der Scraper durchsucht alle **32 europäischen Vinted-Märkte**:

🇦🇹 Österreich · 🇧🇪 Belgien · 🇭🇷 Kroatien · 🇨🇾 Zypern · 🇨🇿 Tschechien · 🇩🇰 Dänemark · 🇪🇪 Estland · 🇫🇮 Finnland · 🇫🇷 Frankreich · 🇩🇪 Deutschland · 🇬🇷 Griechenland · 🇭🇺 Ungarn · 🇮🇪 Irland · 🇮🇹 Italien · 🇱🇻 Lettland · 🇱🇹 Litauen · 🇱🇺 Luxemburg · 🇲🇹 Malta · 🇳🇱 Niederlande · 🇵🇱 Polen · 🇵🇹 Portugal · 🇷🇴 Rumänien · 🇸🇰 Slowakei · 🇸🇮 Slowenien · 🇪🇸 Spanien · 🇸🇪 Schweden · 🇨🇭 Schweiz · 🇬🇧 Großbritannien · 🇳🇴 Norwegen · 🇷🇺 Russland · 🇺🇦 Ukraine · 🇧🇬 Bulgarien

---

## 🔍 Standort-Erkennung

Die Standort-Erkennung nutzt einen **zweistufigen Ansatz**:

1. **⚡ API Pre-Check** – Prüft ob `user.country_title` / `user.city` im API-Response enthalten sind (sofort, kein Browser nötig)
2. **🎭 Playwright Fallback** – Nur wenn die API keine Daten hat, wird Chromium gestartet und die Artikelseite gescraped

Das spart massiv Zeit und löst das Österreich-Problem (URLs zeigen immer auf `vinted.de`, egal welches Land).

---

## 📝 Logs verstehen

| Symbol | Bedeutung |
|--------|-----------|
| ✅ | Erfolgreich |
| ❌ | Fehler |
| ⚡ | Standort aus API (schnell) |
| 🔄 | Session wird erneuert |
| 🍪 | Cookie-Aktion |
| 🆕 | Neue Artikel gefunden! |
| ⏳ | Wartet |
| 🚨 | Blocker/kritischer Fehler |

---

## 🎯 Performance-Tipps

1. **Suchintervall erhöhen** – `CHECK_INTERVAL` in `data_discord.py` / `data_telegram.py` anpassen
2. **Weniger Artikel pro Seite** – `per_page: 10` statt `20`
3. **VPN nutzen** – Andere IP = Weniger Blockaden
4. **Docker nutzen** – Stabiler als lokale Ausführung

---

## 📄 Lizenz

Made by **python_tutorials_de** 🎓

Gern nutzen, verändern, teilen – nur mit Nennung des Autors! ✨