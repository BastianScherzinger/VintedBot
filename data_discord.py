################################################################################
#                                                                              #
#  🔍 VINTED SCRAPER FÜR DISCORD (data_discord.py)                            #
#                                                                              #
#  Diese Datei wird von main.py als separater Prozess gestartet!              #
#  Sie läuft im Hintergrund und sucht kontinuierlich nach neuen Artikeln.    #
#                                                                              #
#  WICHTIG: Diese Datei läuft UNABHÄNGIG - nicht im selben Prozess!           #
#           Das heißt: Der Bot reagiert noch auf Befehle während dies läuft   #
#                                                                              #
################################################################################

import sys
sys.stdout.reconfigure(line_buffering=True)  # Text sofort anzeigen

################################################################################
# IMPORTS - Was wir brauchen
################################################################################
import time      # Für Wartezeiten (sleep)
import json      # Für JSON-Datei-Verarbeitung
import requests  # Für HTTP-Requests zu Vinted
from datetime import datetime  # Für Zeitstempel
from dotenv import load_dotenv  # Tokens laden
import os        # Umgebungsvariablen
from time import sleep  # Wartezeit zwischen Requests
import random    # Für Zufallswerte

# .env laden (mit Discord Token)
load_dotenv()

################################################################################
# ARGUMENTE - Was main.py uns übergeben hat
################################################################################
# main.py startet diese Datei so: python data_discord.py [CHANNEL_ID] [SUCHBEGRIFF]
# Diese Argumente extrahieren wir hier:

if len(sys.argv) > 1:
    CHANNEL_ID = sys.argv[1]  # Erste Argument: Discord Channel ID
else:
    print("❌ Keine Channel ID übergeben!")
    sys.exit(1)  # Beende das Programm mit Fehler

# Suchbegriff aus Argument
if len(sys.argv) > 2:
    SUCHBEGRIFF = " ".join(sys.argv[2:])  # Alle restlichen Argumente kombinieren
else:
    SUCHBEGRIFF = os.getenv("SUCHBEGRIFF", "sneaker")  # Fallback: "sneaker"

TOKEN_DISCORD = os.getenv("DISCORD_TOKEN")  # Discord Token laden

# Start-Meldung
print(f"🔍 Starte Scraper mit Begriff: '{SUCHBEGRIFF}'")
print(f"📌 Channel ID: {CHANNEL_ID}")
print(f"🤖 Token geladen: {TOKEN_DISCORD is not None}")

################################################################################
# KONFIGURATION - Einstellungen
################################################################################
CHECK_INTERVAL = 40  # Alle 40 Sekunden prüfen
SEEN_FILE = "seen.json"  # Datei mit bereits gesehenen Artikeln
LOG_FILE = "log.json"  # Datei mit Suchlogs
MAX_REQUESTS_BEFORE_RENEWAL = 50  # Session erneuern nach 50 Requests
REQUEST_COUNT = 0  # Zähler für Requests
LAST_COOKIE_REFRESH = time.time()  # Letzte Zeit als wir Cookies geholt haben
COOKIE_REFRESH_INTERVAL = 600  # 10 Minuten in Sekunden

################################################################################
# USER-AGENTS - Verschiedene Browser "Gesichter"
################################################################################
# Damit sieht Vinted nicht, dass wir ein Bot sind (mehrere verschiedene verwenden)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0",
]

################################################################################
# HTTP SESSION - Verbindung zu Vinted
################################################################################
# Eine "Session" ist wie ein Gespräch mit einer Website.
# Sie speichert Cookies und Headers damit wir näher wie ein echter Browser aussehen.
session = requests.Session()
session.headers.update({
    "User-Agent": random.choice(USER_AGENTS),  # Zufälligen User-Agent wählen
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "de-DE,de;q=0.9",
    "Referer": "https://www.vinted.de/",
    "Origin": "https://www.vinted.de",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
})

################################################################################
# FUNKTION: erneuere_session()
################################################################################
# Diese Funktion erstellt eine komplett neue Session
# Das ist wichtig, damit wir nicht blockiert werden!
def erneuere_session():
    """Erstelle eine neue Session mit frischem User-Agent und Cookies"""
    global session, REQUEST_COUNT
    print("🔄 Session wird erneuert...")
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),  # Neuer zufälliger User-Agent
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "de-DE,de;q=0.9",
        "Referer": "https://www.vinted.de/",
        "Origin": "https://www.vinted.de",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    })
    REQUEST_COUNT = 0  # Zähler zurücksetzen
    cookie_holen()  # Neue Cookies holen

################################################################################
# FUNKTION: log_suche()
################################################################################
# Diese Funktion speichert jeden Suchbegriff mit Datum/Uhrzeit
def log_suche(begriff):
    """Speichere den Suchbegriff mit Timestamp in log.json"""
    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Aktuelle Zeit formatieren
    try:
        # Versuche alte Logs zu lesen
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            daten = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Falls Datei nicht existiert oder leer ist, starte mit neuer Liste
        daten = []
    
    # Füge neuen Eintrag hinzu
    daten.append({"zeit": jetzt, "suchbegriff": begriff})
    
    # Speichere alles zurück
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=4, ensure_ascii=False)


################################################################################
# FUNKTION: lade_gesehene_ids()
################################################################################
# Liest die Datei mit Artikel-IDs die wir schon an Discord gesendet haben
def lade_gesehene_ids():
    """Lade alle ID-Nummern von Artikeln die wir schon gesehen haben"""
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))  # Gebe als "Set" zurück (schneller zu vergleichen)
    except (FileNotFoundError, json.JSONDecodeError):
        return set()  # Falls Datei leer: leeres Set


################################################################################
# FUNKTION: speichere_gesehene_ids()
################################################################################
# Speichert welche Artikel wir schon gesehen haben
def speichere_gesehene_ids(ids):
    """Speichere die Artikel-IDs in seen.json"""
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids), f, indent=4)


################################################################################
# FUNKTION: sende_discord_nachricht()
################################################################################
# Sende eine Nachricht an Discord über die API
def sende_discord_nachricht(text, bild=None):
    """Sende eine Nachricht an Discord mittels API mit Retry-Logic"""
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages"
    headers = {
        "Authorization": f"Bot {TOKEN_DISCORD}",  # Authentifizierung
        "Content-Type": "application/json"
    }
    
    # Baue Nachricht zusammen
    if bild:
        # Mit Bild und Text (Embed)
        payload = {
            "embeds": [{
                "description": text,
                "color": 0x00b4d8,  # Blauton
                "image": {"url": bild}
            }]
        }
    else:
        # Nur Text
        payload = {"content": text}

    max_versuche = 3
    for versuch in range(max_versuche):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code in [200, 201]:
                print(f"✅ Nachricht gesendet!")
                return
            elif response.status_code == 429:
                # Rate limit - exponentiell warten
                wartezeit = (versuch + 1) * 60
                print(f"⏱️ Discord Rate Limit! Warte {wartezeit}s...")
                time.sleep(wartezeit)
            else:
                print(f"⚠️ Discord API Fehler {response.status_code} (Versuch {versuch+1}/{max_versuche}): {response.text}")
                if versuch < max_versuche - 1:
                    time.sleep(5)
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Discord Verbindungsfehler (Versuch {versuch+1}/{max_versuche}): {e}")
            if versuch < max_versuche - 1:
                wartezeit = (2 ** versuch) * 5  # 5s, 10s, 20s
                print(f"⏳ Warte {wartezeit}s...")
                time.sleep(wartezeit)
        except requests.exceptions.Timeout:
            print(f"⏱️ Discord Timeout (Versuch {versuch+1}/{max_versuche})")
            if versuch < max_versuche - 1:
                wartezeit = (2 ** versuch) * 5
                print(f"⏳ Warte {wartezeit}s...")
                time.sleep(wartezeit)
        except Exception as e:
            print(f"❌ Discord Fehler (Versuch {versuch+1}/{max_versuche}): {e}")
            if versuch < max_versuche - 1:
                wartezeit = (2 ** versuch) * 5
                print(f"⏳ Warte {wartezeit}s...")
                time.sleep(wartezeit)


################################################################################
# FUNKTION: cookie_holen()
################################################################################
# Verbinde zu Vinted um Cookies zu bekommen (damit sieht es aus wie echter Browser)
def cookie_holen():
    """Hole Cookies von Vinted.de - wichtig für Anti-Bot Detection"""
    print("🍪 Hole Cookie von Vinted...")
    max_intentos = 5  # Erhöht auf 5 Versuche
    for intento in range(max_intentos):
        try:
            session.get("https://www.vinted.de", timeout=15)  # Timeout erhöht
            print("✅ Cookie erhalten!")
            return
        except requests.exceptions.ConnectionError as e:
            print(f"⚠️ Verbindungsfehler Versuch {intento + 1}/{max_intentos}: {e}")
            if intento < max_intentos - 1:
                wartezeit = (2 ** intento) * 3  # 3s, 6s, 12s, 24s, 48s exponentiell
                print(f"⏳ Warte {wartezeit}s bevor erneut versucht wird...")
                time.sleep(wartezeit)
        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout Versuch {intento + 1}/{max_intentos}")
            if intento < max_intentos - 1:
                wartezeit = (2 ** intento) * 3
                print(f"⏳ Warte {wartezeit}s bevor erneut versucht wird...")
                time.sleep(wartezeit)
        except Exception as e:
            print(f"⚠️ Fehler beim Cookie abrufen Versuch {intento + 1}/{max_intentos}: {e}")
            if intento < max_intentos - 1:
                wartezeit = (2 ** intento) * 3
                print(f"⏳ Warte {wartezeit}s bevor erneut versucht wird...")
                time.sleep(wartezeit)
        
        # Nach jedem Versuch eine kurze Pause
        if intento < max_intentos - 1:
            time.sleep(2)
    
    print(f"❌ Cookie konnte nach {max_intentos} Versuchen nicht geholt werden!")


################################################################################
# FUNKTION: artikel_suchen()
################################################################################
# Die wichtigste Funktion - suche nach Artikeln auf Vinted
def artikel_suchen(begriff):
    """
    Suche nach Artikeln auf Vinted.de
    
    Diese Funktion:
    1. Erneuert Session bei Bedarf (gegen Blockaden)
    2. Erneuert Cookies regelmäßig
    3. Versucht 5x bei Fehler
    4. Wartet bei 401 und führt Retry durch
    5. Wartet exponentiell bei 429 Rate Limits
    """
    global REQUEST_COUNT, LAST_COOKIE_REFRESH, session
    
    # Schritt 1: Session die 50 Requests überschritten?
    if REQUEST_COUNT >= MAX_REQUESTS_BEFORE_RENEWAL:
        print("📊 Request-Limit erreicht. Erneuere Session...")
        erneuere_session()
    
    # Schritt 2: Sind Cookies älter als 10 Minuten?
    if time.time() - LAST_COOKIE_REFRESH > COOKIE_REFRESH_INTERVAL:
        print("🕐 Cookie-Zeit abgelaufen. Erneuere Cookies...")
        cookie_holen()
        LAST_COOKIE_REFRESH = time.time()
    
    url = "https://www.vinted.de/api/v2/catalog/items"
    params = {"search_text": begriff, "order": "newest_first", "per_page": 20, "page": 1}
    
    # Schritt 3: Versuche bis zu 5 Mal
    max_intentos = 5
    wartezeit_base = 5
    for intento in range(max_intentos):
        try:
            # Watte 1-4 Sekunden (damit sieht es menschlicher aus)
            sleep(random.uniform(1, 4))
            
            # Mache Request zu API
            response = session.get(url, params=params, timeout=15)  # Timeout erhöht
            REQUEST_COUNT += 1  # Erhöhe Zähler
            
            # Fehler 401: Session blockiert - erneuere und versuche nochmal
            if response.status_code == 401:
                print(f"🚨 401 Unauthorized! Erneuere Session (Versuch {intento + 1}/{max_intentos})...")
                erneuere_session()
                if intento < max_intentos - 1:
                    time.sleep(10)
                    continue  # Versuchen nochmal
            
            # Fehler 429: Zu viele Requests - warte exponentiell länger
            if response.status_code == 429:
                warte_zeit = (intento + 1) * 120  # 120, 240, 360, 480, 600 Sekunden
                print(f"⏱️ Rate-Limit erreicht! Warte {warte_zeit}s ({warte_zeit//60} Minuten)... (Versuch {intento + 1}/{max_intentos})")
                time.sleep(warte_zeit)
                if intento < max_intentos - 1:
                    erneuere_session()  # Session erneuern nach Rate Limit
                    continue  # Versuchen nochmal
            
            # Falls erfolgreich: Parser JSON und gebe Artikel zurück
            response.raise_for_status()
            print(f"✅ API-Request erfolgreich ({REQUEST_COUNT} Requests gesamt)")
            return response.json().get("items", [])
            
        except requests.exceptions.HTTPError as e:
            # HTTP Fehler (4xx, 5xx)
            if response.status_code == 401 and intento < max_intentos - 1:
                print(f"⚠️ 401 Fehler, versuche neu... ({intento + 1}/{max_intentos})")
                continue
            print(f"❌ HTTP Fehler {response.status_code}: {e}")
            return []
        except requests.exceptions.ConnectionError as e:
            # Andere Fehler (Netzwerk, Timeout, etc.)
            print(f"❌ Verbindungsfehler beim Abrufen (Versuch {intento + 1}/{max_intentos}): {e}")
            if intento < max_intentos - 1:
                warte_zeit = wartezeit_base * (2 ** intento)  # 5s, 10s, 20s, 40s, 80s exponentiell
                print(f"⏳ Warte {warte_zeit}s bevor erneut versucht wird...")
                time.sleep(warte_zeit)
        except requests.exceptions.Timeout as e:
            print(f"⏱️ Timeout beim Abrufen (Versuch {intento + 1}/{max_intentos}): {e}")
            if intento < max_intentos - 1:
                warte_zeit = wartezeit_base * (2 ** intento)
                print(f"⏳ Warte {warte_zeit}s bevor erneut versucht wird...")
                time.sleep(warte_zeit)
        except Exception as fehler:
            # Andere Fehler (Netzwerk, Timeout, etc.)
            print(f"❌ Fehler beim Abrufen (Versuch {intento + 1}/{max_intentos}): {fehler}")
            if intento < max_intentos - 1:
                warte_zeit = wartezeit_base * (2 ** intento)  # 5s, 10s, 20s, 40s, 80s
                print(f"⏳ Warte {warte_zeit}s bevor erneut versucht wird...")
                time.sleep(warte_zeit)
    
    print(f"❌ Alle {max_intentos} Versuche fehlgeschlagen. Nächster Versuch später!")
    return []  # Falls alle Versuche fehlschlagen


################################################################################
# FUNKTION: neue_artikel_holen()
################################################################################
# Hole neue Artikel und vergleiche mit bereits gesehenen
def neue_artikel_holen(begriff):
    """
    Suche Artikel und filtere: Sind das NEUE?
    
    Logik:
    1. Suche alle Artikel
    2. Vergleiche mit bereits gesehenen
    3. Nur die neuen zurückgeben
    4. Speichere alle als gesehen
    """
    alle = artikel_suchen(begriff)  # Hole alle Artikel
    neue = []
    gesehene = lade_gesehene_ids()  # Lade was wir schon kennen
    
    # Durchlaufe alle Artikel
    for artikel in alle:
        if artikel["id"] not in gesehene:  # ID nicht in "gesehen"?
            neue.append(artikel)  # Neue Artikel hinzufügen
            gesehene.add(artikel["id"])  # Markiere als gesehen
    
    speichere_gesehene_ids(gesehene)  # Speichere aktualisierte Datei
    return neue


################################################################################
# FUNKTION: starten()
################################################################################
# Die Hauptfunktion die alles steuert
def starten():
    """Das Hauptprogramm - die Zentrale des Scrapers"""
    
    # Schritt 1: Verbinde zu Vinted
    cookie_holen()

    # Schritt 2: Sende Start-Nachricht zu Discord
    sende_discord_nachricht(
        f"🚀 **Vinted Scraper gestartet!**\n"
        f"🔍 Suchbegriff: `{SUCHBEGRIFF}`\n"
        f"⏱️ Intervall: alle {CHECK_INTERVAL} Sekunden\n"
        f"📲 Neue Artikel erscheinen hier!"
    )

    # Schritt 3: Lade alle existierenden Artikel (als "gesehen" markieren)
    print("⏳ Initialisierung...")
    erstmalig = artikel_suchen(SUCHBEGRIFF)
    gesehene = lade_gesehene_ids()
    for a in erstmalig:
        gesehene.add(a["id"])
    speichere_gesehene_ids(gesehene)
    print(f"✅ {len(erstmalig)} Artikel als gesehen markiert. Warte auf neue...\n")
    log_suche(SUCHBEGRIFF)

    # Schritt 4: HAUPTSCHLEIFE - Ewig Artikel prüfen
    while True:
        time.sleep(CHECK_INTERVAL)  # Warte z.B. 40 Sekunden
        neue = neue_artikel_holen(SUCHBEGRIFF)  # Suche neue Artikel

        # Falls neue gefunden wurden
        if neue:
            print(f"\n🆕 {len(neue)} neuer Artikel!")
            for a in neue:
                sleep(0.3)  # Kurze Pause zwischen Nachrichten
                
                # Extrahiere Bild-URL
                foto = ""
                if a.get("photo") and a["photo"].get("url"):
                    foto = a["photo"]["url"]

                # Formatiere Preis schön
                preis = a.get('price', {})
                preis_text = f"{preis.get('amount', 'N/A')} {preis.get('currency_code', 'EUR')}" if isinstance(preis, dict) else f"{preis} EUR"
                
                # Baue Link zu Artikel
                link = f"https://www.vinted.de/items/{a['id']}"
                
                # Baue Nachricht zusammen
                nachricht = (
                    f"🆕 **Neuer Artikel!**\n\n"
                    f"📦 **{a['title']}**\n"
                    f"💶 {preis_text}\n"
                    f"🔗 {link}"
                )
                
                # Zeige im Terminal was passiert
                print(f"  📦 {a['title']} | 💶 {preis_text}")
                
                # Sende zu Discord!
                sende_discord_nachricht(nachricht, foto)
        else:
            # Keine neuen Artikel - Warte stille
            print(f"⏳ Keine neuen Artikel... ('{SUCHBEGRIFF}')")


################################################################################
# PROGRAMM-EINSTIEG
################################################################################
if __name__ == "__main__":
    starten()  # Starte die Hauptfunktion!
