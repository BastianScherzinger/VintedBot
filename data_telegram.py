import time
import json
from datetime import datetime
import requests
from config import TOKEN
import sys
import random

# ── Config ──────────────────────────────────────────────
CHECK_INTERVAL = 30  # Sekunden
LOG_FILE = "log.json"
SEEN_FILE = "seen.json"
MAX_REQUESTS_BEFORE_RENEWAL = 50  # Session nach N Requests erneuern
REQUEST_COUNT = 0
LAST_COOKIE_REFRESH = time.time()
COOKIE_REFRESH_INTERVAL = 600  # 10 Minuten
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


def sende_telegram(text, bild=None):
    """Sende Nachricht an Telegram mit Retry-Logic"""
    max_versuche = 3
    for versuch in range(max_versuche):
        try:
            if bild:
                url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
                response = requests.post(url, data={"chat_id": Chat_ID, "caption": text, "photo": bild}, timeout=15)
            else:
                url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
                response = requests.post(url, data={"chat_id": Chat_ID, "text": text}, timeout=15)
            
            # Prüfe ob erfolgreich
            if response.status_code == 200:
                print("✅ Telegram Nachricht gesendet!")
                return
            else:
                print(f"⚠️ Telegram HTTP {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError as e:
            print(f"❌ Telegram Verbindungsfehler (Versuch {versuch+1}/{max_versuche}): {e}")
            if versuch < max_versuche - 1:
                wartezeit = (2 ** versuch) * 5  # 5s, 10s, 20s exponentiell
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
    
    log_suche(SUCHBEGRIFF)
    url = "https://www.vinted.de/api/v2/catalog/items"
    params = {"search_text": SUCHBEGRIFF, "order": "newest_first", "per_page": 20, "page": 1}
    
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
                
                print(f"  📦 Titel:  {a['title']}")
                print(f"  💶 Preis:  {preis_text}")
                link = f"https://www.vinted.de/items/{a['id']}"
                
                nachricht = f"🆕 Neuer Artikel!\n\n📦 {a['title']}\n💶 {preis_text}\n🔗 {link}"
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