# 🐳 Docker & Render Tutorial

Dieses Tutorial zeigt dir, wie du den Bot in einem Docker-Container verpackst und auf Render.com hostest. Durch Docker läuft der Bot in einer isolierten Umgebung, genau wie beim Kunden später.

---

## 1. Lokal mit Docker testen
Stelle sicher, dass [Docker Desktop](https://www.docker.com/products/docker-desktop/) installiert ist.

```bash
# 1. Image bauen
docker compose build

# 2. Container starten (im Hintergrund)
docker compose up -d

# 3. Logs anschauen
docker compose logs -f
```

## 2. Deployment auf Render.com
Render ist perfekt für diesen Bot, da er jetzt sehr wenig RAM verbraucht.

### Schritt-für-Schritt:
1. Logge dich auf [Render.com](https://render.com) ein.
2. Klicke auf **New** → **Web Service** (oder **Background Worker** - Background Worker ist besser da kein Port nötig ist).
3. Verknüpfe dein GitHub Repo.
4. **Environment:** Wähle `Docker`.
5. **Plan:** Wähle den `Free` Plan (oder `Starter` für 24/7 ohne Schlafmodus).

### 🔑 Umgebungsvariablen (EXTREM WICHTIG):
Klicke auf den Tab **Environment** und füge folgende Keys hinzu:
- `DISCORD_TOKEN`
- `DISCORD_CHANNEL_ID`
- `MONGODB_URI`
- `PYTHONUNBUFFERED` = `1`

## 3. Warum Docker auf Render?
- **Größe:** Das neue Image ist winzig (~150MB), da wir kein Chromium/Playwright mehr brauchen.
- **Speed:** Der Bot startet in Sekunden.
- **Stateless:** Da wir MongoDB nutzen, ist es egal, dass Render die Festplatte bei jedem Neustart löscht. Deine Daten bleiben sicher in der Cloud.

---

> [!TIP]
> Wenn du den Bot an einen Kunden übergibst, kannst du ihm einfach den Ordner geben. Er muss nur Docker installieren und `docker compose up` tippen. Den Rest erledigt das System.
