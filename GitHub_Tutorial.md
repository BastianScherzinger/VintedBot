# 🐙 GitHub Tutorial - Code sicher hochladen

Dieses Tutorial zeigt dir, wie du deinen Vinted Scraper in ein **privates** GitHub-Repository hochlädst, um ihn vor anderen zu schützen, aber von überall (z.B. Render.com) darauf zuzugreifen.

---

## 1. GitHub Repository erstellen
1. Logge dich auf [GitHub.com](https://github.com) ein.
2. Klicke oben rechts auf das **+** → **New repository**.
3. **Repository name:** z.B. `vinted-scraper`.
4. **WICHTIG:** Wähle **Private** aus (damit nur du den Code sehen kannst).
5. Klicke auf **Create repository**.

## 2. Git lokal vorbereiten
Falls du Git noch nicht installiert hast, lade es hier herunter: [git-scm.com](https://git-scm.com/).

Öffne ein Terminal in deinem Projektordner (`Final Vinted`) und gib Folgendes ein:

```bash
# 1. Git initialisieren
git init

# 2. Alle Dateien hinzufügen
# (.gitignore sorgt dafür, dass deine .env GEHEIM bleibt!)
git add .

# 3. Den ersten Commit erstellen
git commit -m "Initialer Cloud-Ready Build"
```

## 3. Code zu GitHub pushen
Kopiere die Befehle von deiner GitHub-Seite (unter "...or push an existing repository from the command line"):

```bash
git remote add origin https://github.com/DEIN_USERNAME/vinted-scraper.git
git branch -M main
git push -u origin main
```

---

## ⚠️ Wichtige Sicherheitshinweise

> [!CAUTION]
> **NIEMALS die `.env` Datei hochladen!**
> Die `.gitignore` Datei im Ordner verhindert das bereits. Falls du sie manuell hinzufügst, können Fremde deinen Discord-Token und deine Datenbank-Passwörter stehlen.

### Wie man Änderungen hochlädt:
Wenn du Code änderst, machst du einfach:
1. `git add .`
2. `git commit -m "Beschreibung der Änderung"`
3. `git push`

### Verbindung zu Render:
Auf Render.com kannst du jetzt einfach dein GitHub-Konto verknüpfen und dieses private Repository auswählen. Render hat dann Zugriff, der Rest der Welt nicht.
