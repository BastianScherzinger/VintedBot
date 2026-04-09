# 🏁 Kunden-Setup: So startest du deinen Bot

Folge diesen Schritten, um deinen persönlichen Vinted Scraper in Betrieb zu nehmen.

---

## Schritt 1: Discord Bot erstellen
1. Gehe zum [Discord Developer Portal](https://discord.com/developers/applications).
2. Klicke **New Application** → Name vergeben.
3. Menü links: **Bot**.
4. Aktiviere unter **Privileged Gateway Intents**:
   - `Presence Intent`
   - `Server Members Intent`
   - `Message Content Intent` (EXTREM WICHTIG!)
5. Klicke oben auf **Reset Token** oder **Copy Token** → Speichere diesen Token.
6. Lade den Bot auf deinen Server ein (OAuth2 → URL Generator → `bot` + `Administrator` Rechte).

## Schritt 2: Datenbank (MongoDB Atlas) vorbereiten
1. Erstelle einen Account auf [MongoDB.com](https://www.mongodb.com/).
2. Erstelle einen **M0 (Free)** Cluster.
3. Unter **Database Access**: Erstelle einen User (Username + Passwort merken).
4. Unter **Network Access**: Klicke **Add IP Address** → **Allow Access from Anywhere** (0.0.0.0/0).
5. Klicke auf **Database** → **Connect** → **Drivers** → **Python**.
6. Kopiere den `mongodb+srv://...` Connection-String.

## Schritt 3: Den Bot konfigurieren
1. Öffne die Datei `.env` (falls nicht da, kopiere `.env.example` und benenne sie um).
2. Trage deinen `DISCORD_TOKEN` ein.
3. Trage deinen `MONGODB_URI` ein (Passwort im String nicht vergessen!).
4. Trage die `DISCORD_CHANNEL_ID` deines Hauptkanals ein (Rechtsklick auf Kanal → ID kopieren).

## Schritt 4: Starten (Lokal oder Cloud)

### A) Lokal auf dem PC:
1. Installiere Python 3.11.
2. Öffne den Ordner im Terminal.
3. Tippe: `pip install -r requirements.txt`
4. Tippe: `python main.py`

### B) Cloud (Render.com):
1. Lade den Code zu GitHub hoch (siehe GitHub-Tutorial).
2. Erstelle auf Render einen **Background Worker** basierend auf Docker.
3. Trage die Keys aus deiner `.env` unter **Environment** ein.

---

## 🛠️ Befehls-Schnellstart im Discord
1. `!start` — Startet den Scraper.
2. `!new jordan 60` — Erstellt eine neue Suche für Jordans bis 60€.
3. `!status` — Prüft ob der Bot und die Datenbank online sind.

Viel Erfolg beim Snipen! 🎯
