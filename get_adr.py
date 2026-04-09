import re
import asyncio
import json
import os
import requests
from datetime import datetime

# Speicherdateien (Achtung: Auf Render ephemeral!)
LOCATION_ERRORS_FILE = "location_errors.json"
COUNTRY_EMOJI = {
    'Deutschland': '🇩🇪', 'Frankreich': '🇫🇷', 'Österreich': '🇦🇹',
    'Schweiz': '🇨🇭', 'Niederlande': '🇳🇱', 'Belgien': '🇧🇪',
    'Polen': '🇵🇱', 'Spanien': '🇪🇸', 'Italien': '🇮🇹',
    'Schweden': '🇸🇪', 'Dänemark': '🇩🇰', 'Norwegen': '🇳🇴',
    'Großbritannien': '🇬🇧', 'UK': '🇬🇧', 'Vereinigtes Königreich': '🇬🇧',
    'Litauen': '🇱🇹', 'Lettland': '🇱🇻', 'Estland': '🇪🇪',
}

async def get_location_from_url(url, item_id=None, fallback_country=None):
    """
    Extrahiert den Standort direkt aus dem HTML-Quelltext ohne Browser.
    """
    try:
        # Wir führen den Request in einem Thread aus, damit der Bot nicht blockiert
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        def fetch():
            return requests.get(url, headers=headers, timeout=10)
            
        res = await asyncio.to_thread(fetch)
        
        if res.status_code != 200:
            raise Exception(f"Status {res.status_code}")

        html = res.text
        
        # Suche nach Stadt und Land im Vinted-HTML (JSON-LD oder Meta-Tags)
        # Wir suchen nach dem Muster "city":"Berlin","country":"Deutschland"
        city_match = re.search(r'"city":"(.*?)"', html)
        country_match = re.search(r'"country":"(.*?)"', html)
        
        stadt = city_match.group(1) if city_match else None
        land = country_match.group(1) if country_match else fallback_country
        
        if not land and not stadt:
            # Zweiter Versuch: Suche im Titel/Beschreibung falls vorhanden
            if "Gekauft in" in html:
                land = "Unbekannt" # Platzhalter

        emoji = COUNTRY_EMOJI.get(land, '🌍')
        return (stadt, land or "Unbekannt", emoji)

    except Exception as e:
        print(f"⚠️ Location-Fetch fehlgeschlagen ({item_id}): {e}")
        emoji = COUNTRY_EMOJI.get(fallback_country, '🌍')
        return (None, fallback_country or "Unbekannt", emoji)

def extract_location(url):
    """Synchrone Brücke für den Scraper"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(get_location_from_url(url))