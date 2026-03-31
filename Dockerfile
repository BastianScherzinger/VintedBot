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

# Kopiere requirements.txt in den Container
COPY requirements.txt .

# Installiere alle Python-Pakete
# --no-cache-dir = Spart Speicherplatz (keine Cache der Installation)
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere die .env Datei EXPLIZIT (damit Tokens zur Verfügung stehen)
COPY .env .

# Kopiere den ganzen Code in den Container
COPY . .

# Dieser Befehl wird ausgeführt, wenn der Container startet
CMD ["python", "main.py"]
