################################################################################
#                                                                              #
#  ⚙️ KONFIGURATION (config.py)                                               #
#                                                                              #
#  Diese kleine Datei lädt die Telegram-Daten aus der .env Datei             #
#  und macht sie überall im Projekt verfügbar.                               #
#                                                                              #
#  KURZ: config.py = Telegram-Token und Chat-ID Verwaltung                   #
#                                                                              #
################################################################################

import os
import sys
from dotenv import load_dotenv

# UTF-8 Ausgabe für Windows CMD (damit Emojis funktionieren)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
 
# .env Datei laden (mit den geheimen Tokens)
# Versuche aus aktuellem Verzeichnis und Parent-Verzeichnis
load_dotenv()
load_dotenv(".env", override=True)  # Explizit nach .env suchen
 
# Hole den Telegram Bot Token aus .env
# TOKEN ist wie der "Passwort" des Telegram-Bots
# Mit diesem Token kann der Bot Nachrichten senden
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Hole deine Telegram Chat-ID aus .env
# WICHTIG: Das ist deine persönliche Nummer bei Telegram
# Der Bot weiß damit, zu wem er schreiben soll
Chat_ID = int(os.getenv("TELEGRAM_CHAT_ID", "0"))  # "0" falls nicht gesetzt

# ✅ FEHLERPRÜFUNG: Sind die Tokens wirklich geladen?
if not TOKEN or TOKEN == "":
    print("❌ FEHLER: TELEGRAM_TOKEN nicht gefunden!")
    print("   Prüfe: .env Datei existiert und enthält TELEGRAM_TOKEN=...")
    
if Chat_ID == 0:
    print("⚠️ WARNUNG: TELEGRAM_CHAT_ID ist 0 oder nicht gesetzt!")
    print("   Prüfe: .env Datei enthält TELEGRAM_CHAT_ID=...")

print(f"✅ Config geladen - Token: {bool(TOKEN)}, Chat_ID: {Chat_ID}")

################################################################################
#  WAS IST .env?
################################################################################
#  .env ist eine spezielle Textdatei mit "geheimen" Daten:
#
#  .env Datei Beispiel:
#  ---
#  TELEGRAM_TOKEN=123456789:XXXXXXXXXXXXXXXXXXX
#  TELEGRAM_CHAT_ID=987654321
#  DISCORD_TOKEN=xxxxxxxxxxxxxxxxxxxx
#  DISCORD_CHANNEL_ID=123456789012345678
#  ---
#
#  Diese Datei wird:
#  ✅ NICHT in Git hochgeladen (wegen .gitignore)
#  ✅ Lokal auf deinem PC gespeichert
#  ✅ NIEMALS öffentlich geteilt
#
#  DOCKER: Die .env wird mit COPY .env . in den Container kopiert!
#
################################################################################
