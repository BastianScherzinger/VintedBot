# 🚀 Vinted Scraper Bot

## ⚡ Schnellstart

1. **START.html öffnen** (alle Anweisungen da)
2. **Docker installieren**: https://www.docker.com/products/docker-desktop
3. **Tokens holen** (Tab "TOKENS" in START.html)
4. **.env erstellen** mit Tokens
5. **2 Befehle:**
   ```bash
   docker build -t vinted-scraper .
   docker-compose up -d
   ```

---

## 📚 Dokumetation

- **[START.html](START.html)**
- **[CODE_ERKLÄRUNG.md](CODE_ERKLÄRUNG.md)**

---

## 🐳 Docker

```bash
docker-compose up -d       # Starten
docker-compose logs -f     # Logs
docker-compose down        # Stoppen
```
oder versuch mal docker desktop 📚💡

---

## 💡 Tipps & Tricks

### 1. Mehrere Bots für verschiedene Suchbegriffe
Du kannst Telegram/Discord jeweils nur einen Bot registrieren, aber:
- Ein Suchbot für "Nike"
- Ein Suchbot für "Adidas"
- Ein Suchbot für "Supreme"

Starte einfach mehrere `data_discord.py` Prozesse mit verschiedenen Begriffen!

### 2. Log-Viewer anschauen
```bash
python log_viewer.py
```
Zeigt dir ein hübsches Dashboard mit deinen Suchlogs.


### 3. Konfiguriere den User-Agent
In `data_discord.py` & `data_telegram.py` kannst du mehr User-Agents hinzufügen:
```python
USER_AGENTS = [
    "... bestehende ...",
    "Dein neuer User-Agent hier",
]
```

---

## 📝 Logs verstehen

### Terminal Output Bedeutung

| Symbol | Bedeutung |
|--------|-----------|
| ✅ | Erfolgreich |
| ❌ | Fehler |
| 🔄 | Wird erneuert |
| 🍪 | Cookie-Aktion |
| 🆕 | Neue Artikel! |
| ⏳ | Wartet |
| 🚨 | Blocker/Fehler |

---

## 🔍 Debugging

### 1. Terminal Output durchschauen
Der Bot gibt dir viele Info-Nachrichten. Such nach `❌` für Fehler!

### 2. Logs prüfen
- `log.json` → Alle Suchanfragen
- `seen.json` → Gespeicherte Artikel-IDs
- `Terminal` → Live-Output

### 3. Manuell testen
```python
# Teste die API direkt
python -c "
import requests
response = requests.get('https://www.vinted.de/api/v2/catalog/items', 
                       params={'search_text': 'nike', 'per_page': 1})
print(response.status_code)
print(response.json())
"
```

---

## 🎯 Performance-Tipps

1. **Suchintervall erhöhen** - Mehr Wartezeit = Weniger Blockaden
2. **Weniger Artikel** - `per_page: 10` statt `20`
3. **VPN nutzen** - Andere IP = Weniger Blockaden
4. **Discord/Telegram Delays** - Warte zwischen Meldungen

---


---

## 📄 Lizenz

Made by **python_tutorials_de** 🎓

Gern nutzen, verändern, teilen - nur mit Nennung des Autors! ✨

---