################################################################################
# Dockerfile für Vinted Scraper Bot
# 
# Dieses Dockerfile packiert den Bot in einen Docker-Container
# Der Container kann überall laufen: Windows, Mac, Linux, Server, Cloud
################################################################################

# Basis-Image: Python 3.11 auf Linux
# "slim" = klein und schnell (ohne unnötige Pakete)
FROM python:3.11-slim

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# System-Abhängigkeiten für Playwright (Chromium braucht diese Libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxshmfence1 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Kopiere requirements.txt in den Container
COPY requirements.txt .

# Installiere alle Python-Pakete
# --no-cache-dir = Spart Speicherplatz (keine Cache der Installation)
RUN pip install --no-cache-dir -r requirements.txt

# Installiere Playwright Chromium Browser
RUN playwright install chromium

# Kopiere den ganzen Code in den Container
COPY . .

# Erstelle leere JSON-Dateien falls nicht vorhanden
RUN touch seen.json log.json cities.json countries.json location_errors.json

# Health-Check: Prüfe ob Python-Prozess läuft
HEALTHCHECK --interval=60s --timeout=10s --retries=3 \
    CMD python -c "import requests; requests.get('https://www.vinted.de', timeout=10)" || exit 1

# Dieser Befehl wird ausgeführt, wenn der Container startet
CMD ["python", "main.py"]
