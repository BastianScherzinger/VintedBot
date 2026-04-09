import sys
import json
import re
import os
import random
from datetime import datetime
from dotenv import load_dotenv
import asyncio
import requests
from proxy_manager import proxy_manager
from db import lade_gesehene_ids, markiere_als_gesehen, lade_queue as db_lade_queue

from get_adr import get_location_from_url, COUNTRY_EMOJI
load_dotenv()

TOKEN_DISCORD = os.getenv("DISCORD_TOKEN")
if not TOKEN_DISCORD:
    print("❌ Kein DISCORD_TOKEN in .env!")

PAUSE_ZWISCHEN_BEGRIFFEN = 8
MAX_REQUESTS_BEFORE_RENEWAL = 50
COOKIE_REFRESH_INTERVAL = 600

COUNTRY_IDS = list(range(1, 33))

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/121.0.0.0",
]

CONDITION_EMOJIS = {
    "new": "✨ Neu",
    "never_worn": "✨ Neu / Nie getragen",
    "very_good": "⭐ Sehr gut",
    "good": "👍 Gut",
    "fair": "🤔 Mittelmäßig",
    "poor": "📉 Schlecht",
}

# seen-IDs werden jetzt über db.py geladen/gespeichert (MongoDB oder Fallback)

async def sende_discord_nachricht(channel_id, text, bild=None, artikel_link=None):
    if not TOKEN_DISCORD: return
    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {TOKEN_DISCORD}",
        "Content-Type": "application/json"
    }

    buttons = []
    if artikel_link:
        buttons = [{
            "type": 2,
            "style": 5,
            "label": "💰 Auf Vinted kaufen 🤑",
            "url": artikel_link,
            "emoji": {"name": "🔗"}
        }]

    if bild:
        payload = {
            "embeds": [{
                "description": text,
                "color": 0x00b4d8,
                "image": {"url": bild}
            }],
            "components": [{"type": 1, "components": buttons}] if buttons else []
        }
    else:
        payload = {
            "content": text,
            "components": [{"type": 1, "components": buttons}] if buttons else []
        }

    for versuch in range(3):
        try:
            def do_post():
                return requests.post(url, headers=headers, json=payload, timeout=15)
            response = await asyncio.to_thread(do_post)
            if response.status_code in [200, 201]:
                return
            elif response.status_code == 429:
                wartezeit = (versuch + 1) * 60
                await asyncio.sleep(wartezeit)
            else:
                if versuch < 2:
                    await asyncio.sleep(5)
        except Exception:
            if versuch < 2:
                await asyncio.sleep(5)

class AsyncScraperQueue:
    def __init__(self, queue_file):
        self.queue_file = queue_file
        self.session = None
        self.request_count = 0
        self.last_cookie_refresh = 0

    async def lade_queue(self):
        """Lädt die Queue aus MongoDB (Cloud) oder lokaler Datei (Fallback)"""
        return await db_lade_queue(self.queue_file)

    def get_headers(self):
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "de-DE,de;q=0.9",
            "Referer": "https://www.vinted.de/",
            "Origin": "https://www.vinted.de",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
        }

    async def init_session(self):
        while True:
            if self.session:
                self.session.close()
            self.session = requests.Session()
            self.session.headers.update(self.get_headers())
            
            # Proxy setzen
            self.current_proxy = await proxy_manager.get_proxy_async()
            if self.current_proxy:
                self.session.proxies.update(self.current_proxy)
            
            self.request_count = 0
            
            if await self.cookie_holen():
                break

    async def cookie_holen(self):
        proxy_ip = self.current_proxy['http'].split('//')[1] if self.current_proxy else 'Lokal'
        print(f"🍪 Hole API Cookie von Vinted (IP: {proxy_ip})...")
        for i in range(2):
            try:
                def do_get():
                    return self.session.get("https://www.vinted.de", timeout=10)
                resp = await asyncio.to_thread(do_get)
                if resp.status_code == 403:
                    print(f"⚠️ 403 Forbidden beim Cookie holen (Proxy {proxy_ip})")
                    return False
                else:
                    print(f"✅ Cookie erfolgreich geholt (Status {resp.status_code})")
                    return True
            except Exception as e:
                print(f"⚠️ Proxy {proxy_ip} down/fehlerhaft: {type(e).__name__}")
                await asyncio.sleep(1)
        return False

    async def artikel_suchen(self, begriff, max_preis):
        if self.request_count >= MAX_REQUESTS_BEFORE_RENEWAL:
            await self.init_session()

        jetzt = asyncio.get_event_loop().time()
        if jetzt - self.last_cookie_refresh > COOKIE_REFRESH_INTERVAL:
            await self.cookie_holen()
            self.last_cookie_refresh = asyncio.get_event_loop().time()

        url = "https://www.vinted.de/api/v2/catalog/items"
        params = {
            "search_text": begriff,
            "order": "newest_first",
            "per_page": 20,
            "page": 1,
            "country_ids": ",".join(str(i) for i in COUNTRY_IDS),
        }
        if max_preis > 0:
            params["price_to"] = max_preis

        for versuch in range(5):
            try:
                await asyncio.sleep(random.uniform(1, 3))
                def do_req():
                    return self.session.get(url, params=params, timeout=15)
                response = await asyncio.to_thread(do_req)
                self.request_count += 1
                
                if response.status_code in [401, 403]:
                    print(f"⚠️ API Status {response.status_code} für '{begriff}'. Erneuere Session/Proxy...")
                    await self.init_session()
                    await asyncio.sleep(3)
                    continue
                if response.status_code == 429:
                    wartezeit = (versuch + 1) * 30
                    await asyncio.sleep(wartezeit)
                    await self.init_session()
                    continue

                if response.status_code not in [200, 201]:
                    print(f"⚠️ API Status {response.status_code} für '{begriff}'")
                    response.raise_for_status()

                data = response.json()
                items = data.get("items", [])
                return items
            except Exception as e:
                print(f"❌ Proxy-Fehler bei Suche '{begriff}' ({type(e).__name__}). Wechsle Proxy...")
                await self.init_session()
                if versuch < 4:
                    await asyncio.sleep(2)
        return []

    async def check_begriff(self, channel_id, begriff, max_preis, gesehene):
        alle = await self.artikel_suchen(begriff, max_preis)
        neue = []

        for artikel in alle:
            if artikel["id"] not in gesehene:
                neue.append(artikel)
                gesehene.add(artikel["id"])

        # Neue IDs sofort in die Datenbank schreiben
        neue_ids = [a["id"] for a in neue]
        if neue_ids:
            await markiere_als_gesehen(neue_ids)
        if not neue:
            return

        print(f"  🆕 {len(neue)} neuer Artikel für '{begriff}' gefunden!")

        for a in neue:
            await asyncio.sleep(0.4)
            preis_raw = a.get('price', {})
            preis_wert = float(preis_raw.get('amount', 0)) if isinstance(preis_raw, dict) else float(preis_raw or 0)
            if max_preis > 0 and preis_wert > max_preis:
                continue

            preis_text = f"{preis_raw.get('amount', 'N/A')} {preis_raw.get('currency_code', 'EUR')}" if isinstance(preis_raw, dict) else f"{preis_raw} EUR"
            foto = ""
            if a.get("photo") and a["photo"].get("url"):
                foto = a["photo"]["url"]

            artikel_id = a['id']
            artikel_url = f"https://www.vinted.de/items/{artikel_id}"
            land_display = "\n🌍 ❓ Standort unbekannt"

            try:
                api_land = None
                if a.get('user') and a['user'].get('country_title'):
                    api_land = a['user']['country_title']
                elif a.get('country'):
                    api_land = a['country']

                if api_land:
                    stadt = a.get('user', {}).get('city') or a.get('city', '') or ''
                    land = api_land
                    emoji = COUNTRY_EMOJI.get(land, '❓')
                else:
                    stadt, land, emoji = await get_location_from_url(artikel_url)

                land_display = f"\n🌍 {emoji} {stadt + ', ' + land if stadt else land}"
            except Exception:
                pass

            zustand_key = str(a.get('status', 'very_good')).lower().strip()
            zustand = CONDITION_EMOJIS.get(zustand_key, f"📦 {zustand_key}")

            grosse_wert = a.get('size_title') or a.get('size') or None
            grosse = f"\n📏 **Größe:** {grosse_wert}" if grosse_wert else ""

            link = f"https://www.vinted.de/items/{a['id']}"

            nachricht = (
                f"🆕 **Neuer Artikel!**\n\n"
                f"📦 **{a['title']}**\n"
                f"{zustand}\n"
                f"💶 {preis_text}\n"
                f"{land_display}"
                f"{grosse}\n"
                f"🔗 {link}"
            )

            await sende_discord_nachricht(channel_id, nachricht, foto, link)

    async def run(self):
        await self.init_session()
        self.last_cookie_refresh = asyncio.get_event_loop().time()

        queue = await self.lade_queue()
        if not queue:
            if self.session: self.session.close()
            return

        gesehene = await lade_gesehene_ids()
        for eintrag in queue:
            begriff = eintrag["begriff"]
            max_preis = float(eintrag.get("max_preis", 0))
            artikel = await self.artikel_suchen(begriff, max_preis)
            neue_ids = [a["id"] for a in artikel]
            for aid in neue_ids:
                gesehene.add(aid)
            if neue_ids:
                await markiere_als_gesehen(neue_ids)
            print(f"✅ Initialisiere '{begriff}' - Markiere {len(artikel)} Treffer als gesehen.")
            await asyncio.sleep(2)
        print(f"🚀 {self.queue_file} betriebsbereit. Starte endlose Suche...\n")

        try:
            durchlauf = 0
            while True:
                durchlauf += 1
                queue = await self.lade_queue()
                if not queue:
                    await asyncio.sleep(30)
                    continue

                gesehene = await lade_gesehene_ids()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 {self.queue_file} - Durchlauf #{durchlauf} ({len(queue)} Begriffe)")
                for eintrag in queue:
                    channel_id = eintrag["channel_id"]
                    begriff = eintrag["begriff"]
                    max_preis = float(eintrag.get("max_preis", 0))

                    await self.check_begriff(channel_id, begriff, max_preis, gesehene)
                    await asyncio.sleep(PAUSE_ZWISCHEN_BEGRIFFEN)
        except asyncio.CancelledError:
            pass
        finally:
            if self.session:
                self.session.close()

async def starte_queue_async(queue_file):
    scraper = AsyncScraperQueue(queue_file)
    await scraper.run()
