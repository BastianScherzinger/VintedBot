# 🔍 MongoDB Atlas überwachen – Anleitung

So kannst du live sehen, was dein Bot in die Datenbank schreibt:

---

## 1. Einloggen
Gehe auf **https://cloud.mongodb.com** und logge dich ein.

## 2. Zur Datenbank navigieren
- Links im Menü → **"Database"** klicken
- Du siehst deinen Cluster **"VintedBot"**
- Klicke auf **"Browse Collections"**

## 3. Deine Collections (Tabellen)

Du landest in der Datenbank `vinted_bot`. Dort gibt es jetzt diese Collections:

| Collection | Was steht drin? |
|---|---|
| `seen_ids` | Alle Artikel-IDs, die der Bot schon gepostet hat. Jedes Dokument ist `{ _id: 8595172295 }`. |
| `setup_struktur` | Die komplette Kanal-Struktur von `!start` (Kategorien, Kanalnamen, Suchbegriffe, Maxpreise). |
| `custom_searches` | Alle eigenen Suchen, die du per `!new` hinzugefügt hast. |
| `queues` | Die aktuellen Queues (welcher Prozess welche Begriffe sucht). |

## 4. Live-Daten anschauen
- Klicke auf eine Collection, z.B. `seen_ids`
- Du siehst sofort alle Dokumente als JSON-Liste
- Oben gibt es ein **Filter-Feld**: Tippe z.B. `{ _id: 8595172295 }` ein um einen bestimmten Artikel zu finden
- Klicke auf **"Refresh"** (🔄) um neue Einträge zu sehen

## 5. Statistiken
- In der **"Collections"**-Übersicht siehst du pro Collection:
  - **Document Count** = Wie viele Einträge
  - **Storage Size** = Wie viel Speicher belegt
- Unter **"Metrics"** (oben) siehst du Live-Graphen:
  - Verbindungen pro Minute
  - Lese/Schreib-Operationen
  - Speicherverbrauch

## 6. Schnell-Tipps

- **Artikel-ID suchen:** Collection `seen_ids` → Filter: `{ _id: DEINE_ID }`
- **Alle Custom-Suchen sehen:** Collection `custom_searches` → alle `!new` Einträge
- **Daten löschen:** Klicke auf ein Dokument → 🗑️ Icon → "Delete"
- **Alles löschen:** Collection auswählen → "Drop Collection" (⚠️ unwiderruflich!)

---

> 💡 **Tipp:** Du kannst auch die App "MongoDB Compass" (kostenlos) installieren.
> Dort gibst du deinen Connection-String ein und hast eine Desktop-App
> mit der du die Daten noch komfortabler durchsuchen kannst.
