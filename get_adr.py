import re
import asyncio
import json
import os
import requests
from datetime import datetime
from playwright.async_api import async_playwright

LOCATION_ERRORS_FILE = "location_errors.json"

COUNTRY_EMOJI = {
    'Deutschland': '🇩🇪', 'Frankreich': '🇫🇷', 'Österreich': '🇦🇹',
    'Schweiz': '🇨🇭', 'Niederlande': '🇳🇱', 'Belgien': '🇧🇪',
    'Polen': '🇵🇱', 'Spanien': '🇪🇸', 'Italien': '🇮🇹',
    'Schweden': '🇸🇪', 'Dänemark': '🇩🇰', 'Norwegen': '🇳🇴',
    'Griechenland': '🇬🇷', 'Portugal': '🇵🇹', 'Rumänien': '🇷🇴',
    'Tschechien': '🇨🇿', 'Ungarn': '🇭🇺', 'Irland': '🇮🇪',
    'England': '🇬🇧', 'Großbritannien': '🇬🇧', 'UK': '🇬🇧',
    'Vereinigtes Königreich': '🇬🇧', 'Kroatien': '🇭🇷', 'Slowakei': '🇸🇰',
    'Slowenien': '🇸🇮', 'Litauen': '🇱🇹', 'Lettland': '🇱🇻',
    'Estland': '🇪🇪', 'Zypern': '🇨🇾', 'Malta': '🇲🇹',
    'Luxemburg': '🇱🇺', 'Bulgarien': '🇧🇬', 'Serbien': '🇷🇸',
    'Bosnien': '🇧🇦', 'Mazedonien': '🇲🇰', 'Albanien': '🇦🇱',
    'Moldau': '🇲🇩', 'Ukraine': '🇺🇦', 'Russland': '🇷🇺', 'Finnland': '🇫🇮',
}

ALL_COUNTRIES = list(COUNTRY_EMOJI.keys())

BLACKLIST_PATTERNS = [
    r'partner', r'lieferanten', r'zweck', r'cookie', r'datenschutz',
    r'werbung', r'nutzung', r'verarbeitung', r'speichern', r'zustimm',
    r'consent', r'gdpr', r'impressum', r'agb', r'hilfe', r'support',
]

USERNAME_PATTERNS = [
    r'^[a-z]+[a-z0-9]*$',
    r'^[a-z0-9]+(_|-)[a-z0-9]+$',
    r'^[a-zA-Z]{3,20}[0-9]{1,5}$',
]

def _is_username(text: str) -> bool:
    t = text.strip()
    if len(t) > 40 or len(t) < 3:
        return False
    # Städte haben oft Großbuchstaben oder Sonderzeichen
    if re.search(r'[ÄÖÜÀ-ÿA-Z]', t):  # Hat Großbuchstaben → kein Username
        return False
    if re.match(r'^[a-z0-9]+(_|-)[a-z0-9]+$', t):  # user_name123
        return True
    if re.match(r'^[a-zA-Z]{3,15}[0-9]{2,5}$', t):  # camryn1234
        return True
    return False

def _is_blacklisted(text: str) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in BLACKLIST_PATTERNS)

def _clean_location(location: str) -> str:
    """AGGRESSIVE CLEANING: Benutzernamen, Profil-Info, Zeitstempel"""
    location = re.sub(r'\s+', ' ', location)
    location = re.sub(r'[a-z0-9._-]+\s+\d+\s+', '', location, flags=re.IGNORECASE)
    location = re.sub(r'(zuletzt\s+(online|aktiv)\s+vor|online\s+vor):\s*[\d\s.a-zöäüminuted]*', '', location, flags=re.IGNORECASE)
    location = re.sub(r'\d+\s*(s|sec|sekunde|minute|min|stunden?|h|tag|tage|d)\.?\s*', '', location, flags=re.IGNORECASE)
    location = re.sub(r'noch\s+keine\s+bewertungen?', '', location, flags=re.IGNORECASE)
    location = re.sub(r'\d+ bewertungen?', '', location, flags=re.IGNORECASE)
    location = re.sub(r'(reviews?|rezensionen?|rating)', '', location, flags=re.IGNORECASE)
    location = location.replace('  ', ' ').strip('., ')
    return location

def speichere_location_error(artikel_id: str, error_type: str, titel: str = "Unbekannt"):
    """Speichere fehlgeschlagene Location-Extraktion"""
    try:
        try:
            with open(LOCATION_ERRORS_FILE, "r", encoding="utf-8") as f:
                errors = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            errors = []
        
        errors.append({
            "artikel_id": artikel_id,
            "titel": titel,
            "error_type": error_type,
            "zeit": datetime.now().isoformat()
        })
        
        with open(LOCATION_ERRORS_FILE, "w", encoding="utf-8") as f:
            json.dump(errors, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Fehler beim Speichern des Location-Fehlers: {e}")

def speichere_location_success(artikel_id: str, stadt: str, land: str, titel: str = "Unbekannt"):
    """Speichere erfolgreiche Location-Extraktion"""
    try:
        try:
            with open(LOCATION_ERRORS_FILE, "r", encoding="utf-8") as f:
                errors = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            errors = []
        
        errors.append({
            "artikel_id": artikel_id,
            "titel": titel,
            "error_type": "success",
            "stadt": stadt,
            "land": land,
            "zeit": datetime.now().isoformat()
        })
        
        with open(LOCATION_ERRORS_FILE, "w", encoding="utf-8") as f:
            json.dump(errors, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Fehler beim Speichern des Location-Erfolgs: {e}")

async def _methode_1_selektoren(page) -> str | None:
    """Direkte CSS-Selektoren – schnellste Methode"""
    selectors = [
        '[data-testid="item-location"]', '[data-testid="seller-location"]',
        '[data-cy="item-location"]', '[class*="ItemLocation"]',
        '[class*="item-location"]', '[class*="seller-location"]',
        'span[itemprop="addressLocality"]', '[class*="UserInfo"] [class*="location"]',
    ]
    for sel in selectors:
        try:
            els = page.locator(sel)
            count = await els.count()
            for i in range(count):
                text = await els.nth(i).inner_text(timeout=800)
                text = text.strip()
                if text and len(text) < 120 and not _is_blacklisted(text):
                    text_cleaned = _clean_location(text)
                    if text_cleaned and not _is_username(text_cleaned.split(',')[0]):
                        print(f"✅ M1 Selektor: {sel}")
                        return text_cleaned
        except:
            continue
    return None

async def _methode_2_dom_scan(page) -> str | None:
    """Gezielter DOM-Scan mit Kontext-Prüfung"""
    result = await page.evaluate(
        "(countries) => {"
        "const blacklistSelectors = ['footer', 'nav', 'header', '[class*=\"cookie\"]', '[class*=\"banner\"]', '[class*=\"modal\"]'];"
        "const blacklisted = new Set();"
        "blacklistSelectors.forEach(sel => {"
        "try {document.querySelectorAll(sel).forEach(el => {"
        "el.querySelectorAll('*').forEach(child => blacklisted.add(child));"
        "blacklisted.add(el);"
        "});} catch(e) {}"
        "});"
        "const candidates = [];"
        "const all = document.querySelectorAll('span, p, div, li, strong, b, em');"
        "for (const el of all) {"
        "if (blacklisted.has(el)) continue;"
        "if (el.children.length > 2) continue;"
        "const text = el.innerText?.trim();"
        "if (!text || text.length < 3 || text.length > 100) continue;"
        "const hasCountry = countries.some(c => text.includes(c));"
        "if (!hasCountry) continue;"
        "const parentClass = (el.parentElement?.className?.toString() || '').toLowerCase();"
        "const parentId = (el.parentElement?.id || '').toLowerCase();"
        "const isLocationContext = /(locat|addr|city|place|region|seller|user|profil)/i.test(parentClass + parentId);"
        "candidates.push({text, score: isLocationContext ? 2 : 1, len: text.length});"
        "}"
        "if (!candidates.length) return null;"
        "candidates.sort((a, b) => b.score - a.score || a.len - b.len);"
        "return candidates[0].text;"
        "}",
        ALL_COUNTRIES
    )

    if result and not _is_blacklisted(result):
        result_cleaned = _clean_location(result)
        if result_cleaned and not _is_username(result_cleaned.split(',')[0]):
            print(f"✅ M2 DOM-Scan")
            return result_cleaned
    return None

async def _methode_3_flight_data(page) -> str | None:
    """Next.js Flight-Data nach vollständigem Render auslesen"""
    chunks = await page.evaluate("""
        () => {
            if (!window.__next_f || !window.__next_f.length) return [];
            return window.__next_f.map(c => JSON.stringify(c));
        }
    """)
    if not chunks:
        return None
    full = " ".join(chunks)
    city_m = re.search(r'"city"\s*:\s*"([^"]{2,50})"', full)
    country_m = re.search(r'"country(?:_title)?"\s*:\s*"([^"]{2,50})"', full)
    if city_m or country_m:
        city = city_m.group(1) if city_m else ""
        country = country_m.group(1) if country_m else ""
        result = f"{city}, {country}".strip(", ")
        print(f"✅ M3 Flight-Data: {result}")
        return result
    return None

async def _methode_4_api_intercept(page, item_id: str) -> str | None:
    """Scroll simulieren → Vinted macht danach manchmal API-Call"""
    captured = {}

    async def on_response(response):
        if item_id in response.url and "api" in response.url:
            try:
                data = await response.json()
                item = data.get("item", {})
                if item.get("city") or item.get("country"):
                    captured["city"] = item.get("city", "")
                    captured["country"] = item.get("country") or item.get("country_title", "")
            except:
                pass

    page.on("response", on_response)
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
    await page.wait_for_timeout(2000)

    if captured:
        result = f"{captured.get('city', '')}, {captured.get('country', '')}".strip(", ")
        print(f"✅ M4 API-Intercept: {result}")
        return result
    return None

async def _methode_5_html_regex(page) -> str | None:
    """Regex direkt auf gerendertem HTML"""
    html = await page.content()
    m = re.search(r'"city"\s*:\s*"([^"]{2,50})"[^}]{0,200}"country[^"]*"\s*:\s*"([^"]{2,50})"', html)
    if m:
        result = f"{m.group(1).strip()}, {m.group(2).strip()}"
        print(f"✅ M5 HTML-Regex: {result}")
        return result
    return None

async def _methode_6_seller_profil(page, item_id: str) -> str | None:
    """Seller-Profil direkt über API-Endpoint laden"""
    try:
        # Seller-ID aus der Seite lesen (steht im HTML als data-user-id o.ä.)
        seller_id = await page.evaluate("""
            () => {
                // Methode 1: data-Attribute
                const el = document.querySelector('[data-user-id], [data-seller-id], [data-member-id]');
                if (el) return el.dataset.userId || el.dataset.sellerId || el.dataset.memberId;
                
                // Methode 2: Link-Href parsen (/member/12345/)
                const links = Array.from(document.querySelectorAll('a[href*="/member/"]'));
                for (const link of links) {
                    const m = link.href.match(/\/member\/(\d+)/);
                    if (m) return m[1];
                }
                return null;
            }
        """)

        if not seller_id:
            return None

        # Direkt die Profil-API aufrufen statt die Seite laden
        profil_url = f"https://www.vinted.de/api/v2/users/{seller_id}"
        print(f"🔍 Seller-API: {profil_url}")

        profil_page = await page.context.new_page()
        await profil_page.goto(profil_url, wait_until="commit", timeout=10000)
        content = await profil_page.content()
        await profil_page.close()

        # JSON aus Response parsen
        json_m = re.search(r'\{.*\}', content, re.DOTALL)
        if json_m:
            try:
                data = json.loads(json_m.group())
                user = data.get("user", {})
                city = user.get("city", "")
                country = user.get("country_title", "") or user.get("country", "")
                if city or country:
                    result = f"{city}, {country}".strip(", ")
                    print(f"✅ M6 Seller-API: {result}")
                    return result
            except:
                pass

        return None
    except:
        return None

async def get_location_from_url(url: str) -> tuple:
    """Extrahiert Land und Stadt mit Benutzernamen-Filter (kaufmancamryn Muster)"""
    match = re.search(r'/items/(\d+)', url)
    if not match:
        return (None, 'Unbekannt', '❓')
    
    item_id = match.group(1)
    
    domain_map = {
        'vinted.de': 'Deutschland', 'vinted.fr': 'Frankreich',
        'vinted.at': 'Österreich', 'vinted.co.uk': 'Großbritannien',
        'vinted.pl': 'Polen', 'vinted.es': 'Spanien',
        'vinted.it': 'Italien', 'vinted.nl': 'Niederlande',
        'vinted.be': 'Belgien', 'vinted.se': 'Schweden',
        'vinted.cz': 'Tschechien', 'vinted.hu': 'Ungarn',
        'vinted.pt': 'Portugal', 'vinted.ro': 'Rumänien',
        'vinted.lt': 'Litauen', 'vinted.lu': 'Luxemburg',
        'vinted.sk': 'Slowakei', 'vinted.fi': 'Finnland',
        'vinted.gr': 'Griechenland', 'vinted.dk': 'Dänemark',
    }

    fallback_country = None
    for domain, country_name in domain_map.items():
        if domain in url:
            fallback_country = country_name
            break

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                locale="de-DE",
                extra_http_headers={"Accept-Language": "de-DE,de;q=0.9"}
            )
            page = await context.new_page()

            captured = {}
            async def on_response(response):
                if item_id in response.url and "api" in response.url:
                    try:
                        data = await response.json()
                        item = data.get("item", {})
                        if item.get("city") or item.get("country"):
                            captured["city"] = item.get("city", "")
                            captured["country"] = item.get("country") or item.get("country_title", "")
                            print(f"✅ API-Intercept früh: {response.url}")
                    except:
                        pass
            page.on("response", on_response)



            await page.goto(url, wait_until="networkidle", timeout=20000)
            await page.wait_for_timeout(1500)
            
            # Cookie-Banner wegklicken → Vinted lädt danach mehr Daten
            cookie_selectors = [
                'button:has-text("Alle zulassen")',
                'button:has-text("Akzeptieren")',
                '[data-testid="cookie-accept-all"]',
            ]
            for sel in cookie_selectors:
                try:
                    btn = page.locator(sel).first
                    if await btn.is_visible(timeout=1500):
                        await btn.click()
                        await page.wait_for_timeout(1500)
                        break
                except:
                    continue

            location = None
            location = await _methode_1_selektoren(page)
            if not location:
                location = await _methode_2_dom_scan(page)
            if not location:
                location = await _methode_3_flight_data(page)
            if not location and captured:
                location = f"{captured.get('city', '')}, {captured.get('country', '')}".strip(", ")
                print(f"✅ Früh-API: {location}")
            if not location:
                location = await _methode_5_html_regex(page)
            if not location:
                location = await _methode_4_api_intercept(page, item_id)
            if not location:
                location = await _methode_6_seller_profil(page, item_id)

            await browser.close()

            if location:
                # STADT/LAND TRENNUNG + BENUTZER-FILTER
                country = None
                city = None
                
                for known_country in ALL_COUNTRIES:
                    if known_country in location:
                        country = known_country
                        idx = location.rfind(known_country)
                        potential_city = location[:idx].strip().rstrip(',').strip()
                        
                        # FILTER: Entferne Benutzernamen
                        if potential_city and _is_username(potential_city):
                            potential_city = None
                        
                        if potential_city:
                            if ',' in potential_city:
                                potential_city = potential_city.split(',')[-1].strip()
                            if len(potential_city) < 60 and potential_city:
                                city = potential_city
                        break
                
                if not country:
                    country = 'Unbekannt'
                
                emoji = COUNTRY_EMOJI.get(country, '❓')
                return (city, country, emoji)
            
            # FALLBACK: Land aus URL
            if fallback_country:
                print(f"⚠️ Fallback: {fallback_country}")
                emoji = COUNTRY_EMOJI.get(fallback_country, '❓')
                speichere_location_error(item_id, "no_city_found_used_url_fallback")
                return (None, fallback_country, emoji)
            
            speichere_location_error(item_id, "location_extraction_failed")
            return (None, 'Unbekannt', '❓')
    
    except asyncio.TimeoutError:
        print(f"⏱️ Timeout: {url}")
        speichere_location_error(item_id, "timeout")
        if fallback_country:
            emoji = COUNTRY_EMOJI.get(fallback_country, '❓')
            return (None, fallback_country, emoji)
        return (None, 'Unbekannt', '❓')
    
    except Exception as e:
        print(f"❌ Fehler: {e}")
        speichere_location_error(item_id, f"exception_{type(e).__name__}")
        if fallback_country:
            emoji = COUNTRY_EMOJI.get(fallback_country, '❓')
            return (None, fallback_country, emoji)
        return (None, 'Unbekannt', '❓')


def extract_location(url: str) -> tuple:
    """Synchrone Wrapper"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(get_location_from_url(url))


if __name__ == "__main__":
    test_url = input("Vinted-Link eingeben: ").strip()
    city, country, emoji = extract_location(test_url)
    print(f"\n✅ Ergebnis:")
    print(f"  Stadt: {city}")
    print(f"  Land: {country}")
    print(f"  Emoji: {emoji}")
    print(f"\n  Display: {emoji} {city + ', ' + country if city else country}")
