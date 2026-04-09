# Basis-Image: Schlankes Python 3.11
FROM python:3.11-slim

# Arbeitsverzeichnis
WORKDIR /app

# Installiere minimale System-Abhängigkeiten
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Den restlichen Code kopieren
COPY . .

# Umgebungsvariablen für Python (Output sofort anzeigen)
ENV PYTHONUNBUFFERED=1

# Start-Befehl
CMD ["python", "main.py"]
