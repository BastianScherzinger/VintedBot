import requests
import random
import time
import asyncio
import threading

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.dead_proxies = set()
        self.last_fetch = 0
        self.fetch_cooldown = 180  # 3 Minuten Cooldown zwischen den großen Downloads
        self._lock = threading.Lock()

    def load_proxies(self):
        print("🔄 ProxyManager: Suche nach kostenlosen Proxies im Internet...")
        gestartet = time.time()
        neu = []

        urls = [
            "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
            "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&proxy_format=ipport&format=text",
            "https://www.proxy-list.download/api/v1/get?type=https",
            "https://www.proxy-list.download/api/v1/get?type=http",
            "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
            "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
            "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies_anonymous/http.txt",
            "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
            "https://raw.githubusercontent.com/RX4096/proxy-list/main/online/http.txt",
            "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
            "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
            "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
            "https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt",
            "https://raw.githubusercontent.com/ErcinDedeoglu/proxies/main/proxies/http.txt",
            "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt",
            "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
            "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
            "https://spys.me/proxy.txt",
            "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http",
        ]

        for url in urls:
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    # Geonode gibt JSON zurück
                    if "geonode" in url:
                        try:
                            data = resp.json()
                            for item in data.get("data", []):
                                ip_port = f"{item['ip']}:{item['port']}"
                                if ip_port not in neu and ip_port not in self.dead_proxies:
                                    neu.append(ip_port)
                        except Exception:
                            pass
                        continue

                    lines = resp.text.split('\n')
                    for line in lines:
                        line = line.strip()
                        if ":" in line:
                            parts = line.split(" ")
                            ip_port = parts[0]
                            ip_parts = ip_port.split(":")
                            if len(ip_parts) == 2 and ip_parts[1].isdigit():
                                if ip_port not in neu and ip_port not in self.dead_proxies:
                                    neu.append(ip_port)
            except Exception:
                pass

        random.shuffle(neu)

        with self._lock:
            self.proxies = neu
            self.last_fetch = time.time()

        dauer = round(time.time() - gestartet, 1)
        print(f"🌍 ProxyManager: {len(self.proxies)} Proxies in {dauer}s geladen.")

    def validate_proxy(self, proxy_str: str, timeout: int = 4) -> bool:
        """Schneller Health-Check: Proxy gegen eine neutrale URL testen."""
        proxy_dict = {
            "http": f"http://{proxy_str}",
            "https": f"http://{proxy_str}"
        }
        try:
            resp = requests.get(
                "http://httpbin.org/ip",
                proxies=proxy_dict,
                timeout=timeout
            )
            return resp.status_code == 200
        except Exception:
            return False

    def mark_dead(self, proxy_str: str):
        """Proxy als tot markieren damit er nicht nochmal benutzt wird."""
        with self._lock:
            self.dead_proxies.add(proxy_str)
            if proxy_str in self.proxies:
                self.proxies.remove(proxy_str)

    async def get_proxy_async(self, validate: bool = False):
        """Liefert asynchron einen zufälligen Proxy aus der Liste."""
        # 15% Chance, die eigene (lokale) IP zu testen
        if random.random() < 0.15:
            return None

        # Nachschub holen, wenn Liste leer oder zu alt
        with self._lock:
            need_reload = len(self.proxies) < 10 or time.time() - self.last_fetch > self.fetch_cooldown

        if need_reload:
            await asyncio.to_thread(self.load_proxies)

        with self._lock:
            if not self.proxies:
                print("⚠️ ProxyManager: Keine Proxies gefunden!")
                return None
            proxy_str = self.proxies.pop(0)

        # Optional: Proxy vor Benutzung validieren (langsamer, aber zuverlässiger)
        if validate:
            is_valid = await asyncio.to_thread(self.validate_proxy, proxy_str)
            if not is_valid:
                self.mark_dead(proxy_str)
                return await self.get_proxy_async(validate=True)

        return {
            "http": f"http://{proxy_str}",
            "https": f"http://{proxy_str}",
            "_raw": proxy_str  # Für mark_dead() falls der Proxy später versagt
        }

# Eine globale Instanz, damit alle Tasks auf den selben Pool zugreifen
proxy_manager = ProxyManager()
