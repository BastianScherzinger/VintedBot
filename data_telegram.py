import time
import json
import re
from datetime import datetime
import requests
from config import TOKEN
import sys
import random
from get_adr import extract_location

# ── Config ──────────────────────────────────────────────
CHECK_INTERVAL = 30  # Sekunden
LOG_FILE = "log.json"
SEEN_FILE = "seen.json"
MAX_REQUESTS_BEFORE_RENEWAL = 50  # Session nach N Requests erneuern
REQUEST_COUNT = 0
LAST_COOKIE_REFRESH = time.time()
COOKIE_REFRESH_INTERVAL = 600  # 10 Minuten

# Länder für die Suche (Vinted API country_ids)
COUNTRY_FLAGS = {
    1: "🇦🇹", 2: "🇧🇪", 3: "🇭🇷", 4: "🇨🇾", 5: "🇨🇿", 6: "🇩🇰", 7: "🇪🇪", 8: "🇫🇮", 9: "🇫🇷", 10: "🇩🇪",
    11: "🇬🇷", 12: "🇭🇺", 13: "🇮🇪", 14: "🇮🇹", 15: "🇱🇻", 16: "🇱🇹", 17: "🇱🇺", 18: "🇲🇹", 19: "🇳🇱", 20: "🇵🇱",
    21: "🇵🇹", 22: "🇷🇴", 23: "🇸🇰", 24: "🇸🇮", 25: "🇪🇸", 26: "🇸🇪", 27: "🇨🇭", 28: "🇬🇧",
}

# Zustand-Emojis
CONDITION_EMOJIS = {
    "new": "✨ Neu",
    "never_worn": "✨ Neu",
    "very_good": "⭐ Sehr gut",
    "good": "👍 Gut",
    "fair": "🤔 Mittelmäßig",
    "poor": "📉 Schlecht",
    "neu": "✨ Neu",
    "sehr gut": "⭐ Sehr gut",
    "gut": "👍 Gut",
    "mittelmäßig": "🤔 Mittelmäßig",
    "schlecht": "📉 Schlecht",
}

CITIES_FILE = "cities.json"  # Datei für Stadt-Tracking
COUNTRIES_FILE = "countries.json"  # Datei für Land-Tracking

# Hilfsfunktion: Speichere Städte
def speichere_stadt(stadt, land, emoji):
    """Speichere gefundene Stadt in cities.json"""
    try:
        # 🧹 VALIDIERUNG - Stelle sicher, dass stadt/land sauber sind
        if not stadt or not land or land == "Unbekannt":
            return
        
        # NEUE LOGIK: Trenne ungültige Texte die mit Stadt/Land vermischt sind
        # Pattern: "username Noch keine Bewertungen Bruxelles, Belgien"
        # Extrahiere nur "Bruxelles, Belgien" Teil
        
        # Entferne Bewertungs-Labels
        stadt = re.sub(r'noch\s+keine\s+bewertungen?', '', stadt, flags=re.IGNORECASE)
        stadt = re.sub(r'\d+\s+bewertungen?', '', stadt, flags=re.IGNORECASE)
        stadt = re.sub(r'(reviews?|rezensionen?)', '', stadt, flags=re.IGNORECASE)
        
        # Wenn Stadt mehrere Kommas hat, nimm den letzten Teil (Stadt, Land)
        if ',' in stadt:
            parts = [p.strip() for p in stadt.split(',')]
            # Nimm letzten 2 Teile wenn mehr als 2 Kommas
            if len(parts) >= 2:
                stadt = parts[-2]  # Stadt
                land = parts[-1]    # Land
        
        # Entferne "Zuletzt online" Metadaten aus Stadt
        stadt = re.sub(r'(zuletzt\s+(online|aktiv)\s+vor|online\s+vor):[^,]*', '', stadt, flags=re.IGNORECASE)
        stadt = re.sub(r'\d+\s*(min|h|d|sec|stunden|tage)', '', stadt, flags=re.IGNORECASE)
        stadt = re.sub(r'[a-z0-9._-]+\s+\d+\s+', '', stadt, flags=re.IGNORECASE)  # Benutzernamen
        stadt = stadt.strip()
        
        # Entferne auch "Zuletzt online" Metadaten aus Land
        land = re.sub(r'(zuletzt\s+(online|aktiv)\s+vor|online\s+vor):[^,]*', '', land, flags=re.IGNORECASE)
        land = re.sub(r'\d+\s*(min|h|d|sec|stunden|tage)', '', land, flags=re.IGNORECASE)
        land = land.strip()
        
        # Vermeide zu lange/ungültige Einträge
        if len(stadt) > 50 or len(land) > 50 or not stadt or not land:
            return
        
        try:
            with open(CITIES_FILE, "r", encoding="utf-8") as f:
                cities = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            cities = []
        
        cities.append({"stadt": stadt, "land": land, "emoji": emoji, "zeit": datetime.now().isoformat()})
        with open(CITIES_FILE, "w", encoding="utf-8") as f:
            json.dump(cities, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Fehler beim Speichern der Stadt: {e}")

# Hilfsfunktion: Speichere Länder
def speichere_land(land, emoji):
    """Speichere gefundenes Land in countries.json"""
    try:
        # 🧹 VALIDIERUNG - Stelle sicher, dass land sauber ist
        if not land or land == "Unbekannt":
            return
        
        # Entferne "Zuletzt online" Metadaten
        land = re.sub(r'(zuletzt\s+(online|aktiv)\s+vor|online\s+vor):[^,]*', '', land, flags=re.IGNORECASE)
        land = re.sub(r'\d+\s*(min|h|d|sec|stunden|tage)', '', land, flags=re.IGNORECASE)
        land = land.strip()
        
        # Vermeide ungültige Einträge
        if len(land) > 50 or not land:
            return
        
        try:
            with open(COUNTRIES_FILE, "r", encoding="utf-8") as f:
                countries = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            countries = []
        
        countries.append({"land": land, "emoji": emoji, "zeit": datetime.now().isoformat()})
        with open(COUNTRIES_FILE, "w", encoding="utf-8") as f:
            json.dump(countries, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Fehler beim Speichern des Landes: {e}")

# Land-Namen zu IDs
COUNTRY_NAMES = {
    1: "Österreich", 2: "Belgien", 3: "Kroatien", 4: "Zypern", 5: "Tschechien", 6: "Dänemark", 
    7: "Estland", 8: "Finnland", 9: "Frankreich", 10: "Deutschland", 11: "Griechenland", 
    12: "Ungarn", 13: "Irland", 14: "Italien", 15: "Lettland", 16: "Litauen", 17: "Luxemburg", 
    18: "Malta", 19: "Niederlande", 20: "Polen", 21: "Portugal", 22: "Rumänien", 23: "Slowakei", 
    24: "Slowenien", 25: "Spanien", 26: "Schweden", 27: "Schweiz", 28: "Großbritannien",
}

# Land-Codes aus URL Paths zuordnen
COUNTRY_FROM_URL = {
    "/at/": (1, "Österreich", "🇦🇹"),
    "/de/": (10, "Deutschland", "🇩🇪"),
    "/fr/": (9, "Frankreich", "🇫🇷"),
    "/it/": (14, "Italien", "🇮🇹"),
    "/es/": (25, "Spanien", "🇪🇸"),
    "/se/": (26, "Schweden", "🇸🇪"),
    "/nl/": (19, "Niederlande", "🇳🇱"),
    "/be/": (2, "Belgien", "🇧🇪"),
    "/ch/": (27, "Schweiz", "🇨🇭"),
    "/pl/": (20, "Polen", "🇵🇱"),
    "/gb/": (28, "Großbritannien", "🇬🇧"),
    "/cz/": (5, "Tschechien", "🇨🇿"),
    "/pt/": (21, "Portugal", "🇵🇹"),
    "/ro/": (22, "Rumänien", "🇷🇴"),
    "/sk/": (23, "Slowakei", "🇸🇰"),
    "/ua/": (31, "Ukraine", "🇺🇦"),
    "/gr/": (11, "Griechenland", "🇬🇷"),
    "/hu/": (12, "Ungarn", "🇭🇺"),
    "/ie/": (13, "Irland", "🇮🇪"),
    "/dk/": (6, "Dänemark", "🇩🇰"),
    "/fi/": (8, "Finnland", "🇫🇮"),
}
# ────────────────────────────────────────────────────────

# User-Agents zur Variation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0",
]

# Leere Platzhalter (werden beim Starten befüllt)
Chat_ID = ""
SUCHBEGRIFF = ""

session = requests.Session()
session.headers.update({
    "User-Agent": random.choice(USER_AGENTS),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "de-DE,de;q=0.9",
    "Referer": "https://www.vinted.de/",
    "Origin": "https://www.vinted.de",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
})

gesehene_ids = set()

def erneuere_session():
    """Erstelle eine neue Session mit frischem User-Agent und Cookies"""
    global session, REQUEST_COUNT
    print("🔄 Session wird erneuert...")
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "de-DE,de;q=0.9",
        "Referer": "https://www.vinted.de/",
        "Origin": "https://www.vinted.de",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
    })
    REQUEST_COUNT = 0
    cookie_holen()

def log_suche(neuer_begriff):
    jetzt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    eintrag = {"zeit": jetzt, "suchbegriff": neuer_begriff}
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            daten = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        daten = []
    daten.append(eintrag)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=4, ensure_ascii=False)
    print(f"✅ Log geschrieben: {jetzt} - {neuer_begriff}")


def sende_telegram_formatted(text, bild=None):
    """Sende formatierte Nachricht an Telegram (HTML)"""
    max_versuche = 3
    for versuch in range(max_versuche):
        try:
            if bild:
                url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
                response = requests.post(url, data={"chat_id": Chat_ID, "caption": text, "photo": bild, "parse_mode": "HTML"}, timeout=15)
            else:
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                response = requests.post(url, data={"chat_id": Chat_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
            
            # Prüfe ob erfolgreich
            if response.status_code == 200:
                print("✅ Telegram Nachricht gesendet!")
                return
            else:
                print(f"⚠️ Telegram HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Telegram Verbindungsfehler (Versuch {versuch+1}/{max_versuche}): {e}")
            if versuch < max_versuche - 1:
                wartezeit = (2 ** versuch) * 5
                print(f"⏳ Warte {wartezeit}s...")
                time.sleep(wartezeit)
        except requests.exceptions.Timeout:
            print(f"⏱️ Telegram Timeout (Versuch {versuch+1}/{max_versuche})")
            if versuch < max_versuche - 1:
                wartezeit = (2 ** versuch) * 5
                print(f"⏳ Warte {wartezeit}s...")
                time.sleep(wartezeit)
        except Exception as e:
            print(f"❌ Telegram Fehler (Versuch {versuch+1}/{max_versuche}): {e}")
            if versuch < max_versuche - 1:
                wartezeit = (2 ** versuch) * 5
                print(f"⏳ Warte {wartezeit}s...")
                time.sleep(wartezeit)


def sende_telegram(text, bild=None):
    """Sende einfache Nachricht an Telegram mit Retry-Logic"""
    max_versuche = 3
    for versuch in range(max_versuche):
        try:
            if bild:
                url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
                response = requests.post(url, data={"chat_id": Chat_ID, "caption": text, "photo": bild}, timeout=15)
            else:
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                response = requests.post(url, data={"chat_id": Chat_ID, "text": text}, timeout=15)
            
            if response.status_code == 200:
                print("✅ Telegram Nachricht gesendet!")
                return
            else:
                print(f"⚠️ Telegram HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Telegram Verbindungsfehler (Versuch {versuch+1}/{max_versuche}): {e}")
            if versuch < max_versuche - 1:
                wartezeit = (2 ** versuch) * 5
                print(f"⏳ Warte {wartezeit}s...")
                time.sleep(wartezeit)
        except requests.exceptions.Timeout:
            print(f"⏱️ Telegram Timeout (Versuch {versuch+1}/{max_versuche})")
            if versuch < max_versuche - 1:
                wartezeit = (2 ** versuch) * 5
                print(f"⏳ Warte {wartezeit}s...")
                time.sleep(wartezeit)
        except Exception as e:
            print(f"❌ Telegram Fehler (Versuch {versuch+1}/{max_versuche}): {e}")
            if versuch < max_versuche - 1:
                wartezeit = (2 ** versuch) * 5
                print(f"⏳ Warte {wartezeit}s...")
                time.sleep(wartezeit)


def lade_gesehene_ids():
    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()
    
def speichere_gesehene_ids(ids):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids), f, indent=4)


def cookie_holen():
    print("🍪 Hole Cookie von Vinted...")
    max_intentos = 5  # Erhöht auf 5 Versuche
    for intento in range(max_intentos):
        try:
            session.get("https://www.vinted.de", timeout=15)  # Timeout erhöht
            print("✅ Cookie erhalten!\n")
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
    
    print(f"❌ Cookie konnte nach {max_intentos} Versuchen nicht geholt werden!\n")


def artikel_suchen():
    global REQUEST_COUNT, LAST_COOKIE_REFRESH, session, SUCHBEGRIFF
    
    # Session erneuern bei zu vielen Requests
    if REQUEST_COUNT >= MAX_REQUESTS_BEFORE_RENEWAL:
        print("📊 Request-Limit erreicht. Erneuere Session...")
        erneuere_session()
    
    # Cookies alle 10 Minuten erneuern
    if time.time() - LAST_COOKIE_REFRESH > COOKIE_REFRESH_INTERVAL:
        print("🕐 Cookie-Zeit abgelaufen. Erneuere Cookies...")
        cookie_holen()
        LAST_COOKIE_REFRESH = time.time()
    
    #log_suche(SUCHBEGRIFF)
    # Alle 32 europäischen Vinted-Länder durchsuchen
    ALL_COUNTRY_IDS = ",".join(str(i) for i in range(1, 33))
    url = "https://www.vinted.de/api/v2/catalog/items"
    params = {"search_text": SUCHBEGRIFF, "order": "newest_first", "per_page": 20, "page": 1, "country_ids": ALL_COUNTRY_IDS}
    
    max_intentos = 5  # Erhöht auf 5 Versuche
    wartezeit_base = 5  # Basis-Wartezeit
    
    for intento in range(max_intentos):
        try:
            # Random Delay zur Vermeidung von Bot-Erkennung (1-4 Sekunden)
            time.sleep(random.uniform(1, 4))
            
            response = session.get(url, params=params, timeout=15)  # Timeout erhöht
            REQUEST_COUNT += 1
            
            # 401 Unauthorized - Session ist blockiert, erneuere sie
            if response.status_code == 401:
                print(f"🚨 401 Unauthorized! Erneuere Session (Versuch {intento + 1}/{max_intentos})...")
                erneuere_session()
                if intento < max_intentos - 1:
                    time.sleep(10)  # Längere Pause nach 401
                    continue
            
            # 429 Too Many Requests - Zu viele Requests, warte länger
            if response.status_code == 429:
                warte_zeit = (intento + 1) * 120  # Exponential backoff: 120, 240, 360, 480, 600 Sekunden
                print(f"⏱️ Rate-Limit erreicht! Warte {warte_zeit}s ({warte_zeit//60} Minuten)... (Versuch {intento + 1}/{max_intentos})")
                time.sleep(warte_zeit)
                if intento < max_intentos - 1:
                    erneuere_session()  # Session erneuern nach Rate Limit
                    continue
            
            response.raise_for_status()
            print(f"✅ API-Request erfolgreich ({REQUEST_COUNT} Requests gesamt)")
            return response.json().get("items", [])
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401 and intento < max_intentos - 1:
                print(f"⚠️ 401 Fehler, versuche neu... ({intento + 1}/{max_intentos})")
                continue
            print(f"❌ HTTP Fehler {response.status_code}: {e}")
            return []
        except requests.exceptions.ConnectionError as e:
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
            print(f"❌ Fehler beim Abrufen (Versuch {intento + 1}/{max_intentos}): {fehler}")
            if intento < max_intentos - 1:
                warte_zeit = wartezeit_base * (2 ** intento)  # 5s, 10s, 20s, 40s, 80s
                print(f"⏳ Warte {warte_zeit}s bevor erneut versucht wird...")
                time.sleep(warte_zeit)
    
    print(f"❌ Alle {max_intentos} Versuche fehlgeschlagen. Nächster Versuch später!")
    return []


def neue_artikel_holen():
    alle_artikel = artikel_suchen()
    neue = []
    global gesehene_ids
    gesehene_ids = lade_gesehene_ids()

    for artikel in alle_artikel:
        if artikel["id"] not in gesehene_ids:
            neue.append(artikel)
            gesehene_ids.add(artikel["id"])
            
    speichere_gesehene_ids(gesehene_ids)
    return neue


def starten():
    cookie_holen()
    print("⏳ Initialisierung – lade aktuelle Artikel...")
    _ = artikel_suchen()
    print(f"✅ {len(gesehene_ids)} Artikel gespeichert. Warte auf neue...\n")

    while True:
        time.sleep(CHECK_INTERVAL)
        neue = neue_artikel_holen()

        if neue:
            print(f"\n🆕 {len(neue)} neuer Artikel gefunden!")
            for a in neue:
                foto = ""
                if a.get("photo") and a["photo"].get("url"):
                    foto = a["photo"]["url"]
                
                preis = a.get('price', {})
                if isinstance(preis, dict):
                    preis_text = f"{preis.get('amount', 'N/A')} {preis.get('currency_code', 'EUR')}"
                else:
                    preis_text = f"{preis} EUR"
                
                # Extrahiere Land und Stadt – ERST aus API-Daten, dann Playwright-Fallback
                artikel_id = a['id']
                artikel_url = f"https://www.vinted.de/items/{artikel_id}"
                print(f"🔍 Extrahiere Standort für Artikel {artikel_id}...")
                try:
                    # Pre-Check: Hat die API schon Location-Daten?
                    api_land = None
                    if a.get('user') and a['user'].get('country_title'):
                        api_land = a['user']['country_title']
                    elif a.get('country'):
                        api_land = a['country']
                    
                    if api_land:
                        # API hat die Antwort → kein Playwright nötig!
                        stadt = a.get('user', {}).get('city') or a.get('city', '') or ''
                        land = api_land
                        from get_adr import COUNTRY_EMOJI
                        emoji = COUNTRY_EMOJI.get(land, '❓')
                        print(f"⚡ Standort aus API: {emoji} {stadt + ', ' + land if stadt else land}")
                        from get_adr import speichere_location_success
                        speichere_location_success(str(artikel_id), stadt, land, a['title'])
                    else:
                        # Kein API-Land → Playwright starten
                        stadt, land, emoji = extract_location(artikel_url)
                        if land == "Unbekannt":
                            from get_adr import speichere_location_error
                            speichere_location_error(str(artikel_id), "location_extraction_failed", a['title'])
                        else:
                            from get_adr import speichere_location_success
                            speichere_location_success(str(artikel_id), stadt, land, a['title'])
                        print(f"✅ Standort via Playwright: {emoji} {stadt + ', ' + land if stadt else land}")
                    
                    speichere_stadt(stadt, land, emoji)  # 🏙️ Speichere Stadt für Dashboard
                    speichere_land(land, emoji)  # 🏙️ Speichere Land für Dashboard
                    if stadt:
                        land_display = f"\n🌍 {emoji} {stadt}, {land}"
                    else:
                        land_display = f"\n🌍 {emoji} {land}"
                except Exception as e:
                    print(f"⚠️ Standort-Fehler: {e}")
                    land_display = "\n🌍 ❓ Standort konnte nicht extrahiert werden"
                
                # Extrahiere Zustand (Condition)
                zustand_key = str(a.get('status', 'very_good')).lower().strip()
                zustand = CONDITION_EMOJIS.get(zustand_key, f"📦 {zustand_key}")
                
                # Extrahiere Größe wenn vorhanden
                grosse = ""
                if a.get('size'):
                    grosse = f"\n📏 Größe: {a.get('size')}"
                
                print(f"  📦 {a['title']} | 💶 {preis_text} | {zustand}")
                link = f"https://www.vinted.de/items/{a['id']}"
                
                nachricht = (
                    f"🆕 Neuer Artikel!\n\n"
                    f"📦 {a['title']}\n"
                    f"{zustand}\n"
                    f"💶 {preis_text}"
                    f"{land_display}"
                    f"{grosse}\n"
                    f"🔗 {link}"
                )
                sende_telegram(nachricht, foto)
        else:
            print(f"⏳ Keine neuen Artikel... (gesamt gesehen: {len(gesehene_ids)})")

# HIER werden die Argumente eingelesen
if __name__ == "__main__":
    if len(sys.argv) > 2:
        Chat_ID = sys.argv[1]
        SUCHBEGRIFF = " ".join(sys.argv[2:])
        starten()
    else:
        print("❌ Fehler: Keine Chat-ID oder Suchbegriff übergeben!")
        sys.exit(1)