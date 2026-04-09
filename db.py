################################################################################
#                                                                              #
#  🗄️ MONGODB ATLAS - DATENBANK MODUL (db.py)                                 #
#                                                                              #
#  Dieses Modul ersetzt alle lokalen .json Dateien durch eine                  #
#  kostenlose MongoDB Atlas Cloud-Datenbank.                                   #
#                                                                              #
#  ════════════════════════════════════════════════════════════════════════════  #
#                                                                              #
#  🔧 WAS DU TUN MUSST (EINMALIG):                                            #
#                                                                              #
#  1. Gehe auf https://www.mongodb.com/atlas und erstelle einen                #
#     kostenlosen Account (mit Google/GitHub einloggen geht am schnellsten).   #
#                                                                              #
#  2. Erstelle einen KOSTENLOSEN "M0" Cluster:                                 #
#     - Klicke "Build a Database" → wähle "M0 FREE"                           #
#     - Region: Frankfurt (eu-central) oder Amsterdam                          #
#     - Cluster Name: z.B. "VintedBot"                                        #
#                     
# bastianscherzinger05_db_user                        
# 4zrkhqIudhxq7xHy                                 #
#  3. Erstelle einen Database-User:                                            #
#     - Unter "Database Access" → "Add New Database User"                      #
#     - Username: z.B. "vintedbot"                                             #
#     - Passwort: z.B. "DeinSicheresPasswort123"                               #
#     - Rolle: "Read and write to any database"
# 
# mongodb+srv://bastianscherzinger05_db_user:<db_password>@vintedbot.k7dbkia.mongodb.net/?appName=VintedBot                                #
#                                                                              #
#  4. Erlaube Zugriff von überall (wichtig für Render!):                       #
#     - Unter "Network Access" → "Add IP Address"                              #
#     - Klicke "Allow Access from Anywhere" (0.0.0.0/0)                        #
#                                                                              #
#  5. Hole deinen Connection-String:                                           #
#     - Gehe zu "Database" → "Connect" → "Drivers" → "Python"                 #
#     - Kopiere den String, er sieht so aus:                                   #
#       mongodb+srv://vintedbot:DeinPasswort@vintedbot.abc123.mongodb.net/     #
#                            
# mongodb+srv://bastianscherzinger05_db_user:<db_password>@vintedbot.k7dbkia.mongodb.net/?appName=VintedBot                                                  #
#  6. Füge den String in deine .env Datei ein:                                 #
#     MONGODB_URI=mongodb+srv://bastianscherzinger05_db_user:<db_password>@vintedbot.k7dbkia.mongodb.net/?appName=VintedBot    #
#                                                                              #
#  7. Auf Render.com: Unter "Environment" den gleichen Key+Value eintragen.    #
#                                                                              #
#  ════════════════════════════════════════════════════════════════════════════  #
#                                                                              #
#  ⚡ FERTIG! Ab jetzt speichert der Bot alle gesehenen Artikel-IDs            #
#     und Queues dauerhaft in der Cloud. Kein Datenverlust mehr                #
#     bei Render-Neustarts!                                                    #
#                                                                              #
################################################################################

import sys
import os
import json
import asyncio
from dotenv import load_dotenv

# Windows-Konsole Emoji-Fix (wie in main.py)
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

load_dotenv()

# ══════════════════════════════════════════════════════════════════════════════
# MongoDB-Verbindung
# ══════════════════════════════════════════════════════════════════════════════
# Wir nutzen "motor" (asynchrones PyMongo), damit der Bot nicht blockiert.
# Falls MONGODB_URI nicht gesetzt ist, fällt der Bot automatisch auf
# lokale .json Dateien zurück (z.B. beim lokalen Testen auf deinem PC).
# ══════════════════════════════════════════════════════════════════════════════

MONGODB_URI = os.getenv("MONGODB_URI")

_db = None       # Globale DB-Referenz (wird beim ersten Aufruf gesetzt)
_client = None   # Globaler Client

def _get_db():
    """Erstellt die MongoDB-Verbindung beim ersten Aufruf (lazy init)."""
    global _db, _client
    if _db is not None:
        return _db

    if not MONGODB_URI:
        print("⚠️ MONGODB_URI nicht in .env gesetzt → Fallback auf lokale .json Dateien.")
        return None

    try:
        import motor.motor_asyncio
        _client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
        _db = _client["vinted_bot"]  # Datenbankname in MongoDB
        print("✅ MongoDB Atlas verbunden!")
        return _db
    except Exception as e:
        print(f"❌ MongoDB Verbindung fehlgeschlagen: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# SEEN-IDs (gesehene Artikel) — Ersetzt seen.json
# ══════════════════════════════════════════════════════════════════════════════
# Collection: "seen_ids"
# Jedes Dokument: { "_id": <artikel_id_als_int> }
# ══════════════════════════════════════════════════════════════════════════════

SEEN_FILE_FALLBACK = "seen.json"

async def lade_gesehene_ids() -> set:
    """Lädt alle gesehenen Artikel-IDs aus MongoDB (oder seen.json als Fallback)."""
    db = _get_db()
    if db is not None:
        try:
            cursor = db["seen_ids"].find({}, {"_id": 1})
            docs = await cursor.to_list(length=100_000)
            ids = {doc["_id"] for doc in docs}
            return ids
        except Exception as e:
            print(f"⚠️ MongoDB Lesen fehlgeschlagen: {e}")

    # Fallback: Lokale Datei (für lokales Testen ohne MongoDB)
    try:
        with open(SEEN_FILE_FALLBACK, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


async def speichere_gesehene_ids(ids: set):
    """Speichert alle gesehenen IDs in MongoDB (oder seen.json als Fallback)."""
    db = _get_db()
    if db is not None:
        try:
            # Nur neue IDs einfügen (upsert vermeidet Duplikate)
            if ids:
                from pymongo import UpdateOne
                ops = [UpdateOne({"_id": aid}, {"$set": {"_id": aid}}, upsert=True) for aid in ids]
                await db["seen_ids"].bulk_write(ops, ordered=False)
            return
        except Exception as e:
            print(f"⚠️ MongoDB Schreiben fehlgeschlagen: {e}")

    # Fallback: Lokale Datei
    with open(SEEN_FILE_FALLBACK, "w", encoding="utf-8") as f:
        json.dump(list(ids), f, indent=4)


async def ist_artikel_gesehen(artikel_id: int) -> bool:
    """Prüft ob ein einzelner Artikel bereits gesehen wurde (schneller als alles laden)."""
    db = _get_db()
    if db is not None:
        try:
            doc = await db["seen_ids"].find_one({"_id": artikel_id})
            return doc is not None
        except Exception:
            pass
    return False


async def markiere_als_gesehen(artikel_ids: list):
    """Markiert eine Liste von Artikel-IDs als gesehen (Batch-Insert)."""
    db = _get_db()
    if db is not None:
        try:
            if artikel_ids:
                from pymongo import UpdateOne
                ops = [UpdateOne({"_id": aid}, {"$set": {"_id": aid}}, upsert=True) for aid in artikel_ids]
                await db["seen_ids"].bulk_write(ops, ordered=False)
            return
        except Exception as e:
            print(f"⚠️ MongoDB Batch-Insert fehlgeschlagen: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# QUEUE-Verwaltung — Ersetzt queue_*.json
# ══════════════════════════════════════════════════════════════════════════════
# Collection: "queues"
# Jedes Dokument: { "_id": "queue_0", "eintraege": [...] }
# ══════════════════════════════════════════════════════════════════════════════

QUEUE_FILE_PATTERN = "queue_{}.json"

async def lade_queue(index_or_file):
    """Lädt eine Queue aus MongoDB (oder lokaler Datei als Fallback)."""
    db = _get_db()

    # Bestimme den Key/Dateinamen
    if isinstance(index_or_file, int):
        queue_key = f"queue_{index_or_file}"
        file_path = QUEUE_FILE_PATTERN.format(index_or_file)
    else:
        queue_key = index_or_file.replace(".json", "")
        file_path = index_or_file

    if db is not None:
        try:
            doc = await db["queues"].find_one({"_id": queue_key})
            if doc:
                return doc.get("eintraege", [])
            return []
        except Exception as e:
            print(f"⚠️ MongoDB Queue-Laden fehlgeschlagen: {e}")

    # Fallback: Lokale Datei
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


async def speichere_queue(index, eintraege):
    """Speichert eine Queue in MongoDB (oder lokaler Datei als Fallback)."""
    db = _get_db()
    queue_key = f"queue_{index}"

    if db is not None:
        try:
            await db["queues"].update_one(
                {"_id": queue_key},
                {"$set": {"eintraege": eintraege}},
                upsert=True
            )
            return
        except Exception as e:
            print(f"⚠️ MongoDB Queue-Speichern fehlgeschlagen: {e}")

    # Fallback: Lokale Datei
    file_path = QUEUE_FILE_PATTERN.format(index)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(eintraege, f, indent=2, ensure_ascii=False)


async def loesche_alle_queues():
    """Löscht alle Queues aus MongoDB (oder lokale queue_*.json Dateien)."""
    db = _get_db()
    if db is not None:
        try:
            await db["queues"].delete_many({})
            return
        except Exception as e:
            print(f"⚠️ MongoDB Queue-Löschen fehlgeschlagen: {e}")

    # Fallback: Lokale Dateien löschen
    from glob import glob
    for f in glob("queue_*.json"):
        try:
            os.remove(f)
        except Exception:
            pass
