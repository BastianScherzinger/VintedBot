################################################################################
#                                                                              #
#  🤖 VINTED SCRAPER BOT - HAUPTDATEI (main.py)                               #
#                                                                              #
#  Dieser Programm startet den Discord Bot und verwaltet alle Befehle.        #
#  KURZ: main.py = Kontrollzentrale des gesamten Bots                         #
#                                                                              #
################################################################################

from glob import glob
import sys
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
sys.stderr.reconfigure(encoding='utf-8')

try:
    ################################################################################
    # IMPORTS
    ################################################################################
    from pyfiglet import figlet_format
    from keep_alive import keep_alive

    import discord
    from discord.ext import commands
    from dotenv import load_dotenv

    import asyncio
    import os
    from scraper_queue import starte_queue_async
    import json
    import math
    import requests
    from db import _get_db, lade_gesehene_ids as db_lade_seen, speichere_queue as db_speichere_queue

    ################################################################################
    # BANNER
    ################################################################################
    banner = figlet_format("Vinted X Discord Bot", font="small")
    print(banner, "\nmade by python_tutorials_de\n")

    ################################################################################
    # GLOBALE VARIABLEN
    ################################################################################
    discord_prozesse      = {}   # Einzelne Prozesse (nicht mehr aktiv genutzt, bleibt für Kompatibilität)
    discord_kanal_ids     = {}   # Zuordnung suchbegriff -> channel_id
    aktive_tasks          = []   # Die laufenden Queue-Prozesse von !start
    aktive_prozess_anzahl = 0    # Wie viele Queue-Prozesse gerade laufen

    QUEUE_FILE = "queue_{}.json"   # queue_0.json, queue_1.json, ...

    ################################################################################
    # HELPER FUNKTIONEN
    ################################################################################
    def get_kanal_key(suchbegriff):
        return suchbegriff[:20].lower()

    def lade_queue(index):
        # Synchroner Fallback für Initialisierung
        try:
            with open(QUEUE_FILE.format(index), "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    async def async_speichere_queue(index, eintraege):
        await db_speichere_queue(index, eintraege)

    def verteile_auf_queues(alle_eintraege, anzahl):
        """Verteilt Einträge per Round-Robin gleichmäßig auf N Listen"""
        queues = [[] for _ in range(anzahl)]
        for i, eintrag in enumerate(alle_eintraege):
            queues[i % anzahl].append(eintrag)
        return queues

    def kuerzeste_queue_index():
        """Gibt den Index der Queue mit den wenigsten Einträgen zurück"""
        if aktive_prozess_anzahl == 0:
            return 0
        kuerzeste = 0
        min_laenge = len(lade_queue(0))
        for i in range(1, aktive_prozess_anzahl):
            l = len(lade_queue(i))
            if l < min_laenge:
                min_laenge = l
                kuerzeste = i
        return kuerzeste

    ################################################################################
    # UMGEBUNGSVARIABLEN
    ################################################################################
    load_dotenv()
    load_dotenv(".env", override=True)

    TOKENDISCORD       = os.getenv("DISCORD_TOKEN")
    DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

    print("\n" + "="*50)
    print(f"✅ Discord Token: {bool(TOKENDISCORD)}")
    print(f"✅ Discord Channel: {bool(DISCORD_CHANNEL_ID)}")
    # MongoDB beim Start sichtbar testen
    _test_db = _get_db()
    if _test_db is not None:
        print(f"✅ MongoDB Atlas: Verbunden (DB: vinted_bot)")
    else:
        print(f"⚠️ MongoDB Atlas: NICHT verbunden → Fallback auf lokale Dateien")
    print("="*50 + "\n")

    if not TOKENDISCORD:
        print("⚠️ DISCORD_TOKEN fehlt in der .env!")
        sys.exit(1)

    ################################################################################
    # DISCORD BOT SETUP
    ################################################################################
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    ################################################################################
    # ON READY
    ################################################################################
    @bot.event
    async def on_ready():
        print(f'✅ Discord Bot eingeloggt als {bot.user}')
        channel_id_str = os.getenv("DISCORD_CHANNEL_ID")
        if channel_id_str:
            try:
                channel = bot.get_channel(int(channel_id_str))
                if channel:
                    await channel.send(
                        "✅ **Vinted Bot ist online!**\n\n"
                        "Schreib `!info` um alle verfügbaren Befehle zu sehen."
                    )
            except Exception as e:
                print(f"⚠️ Start-Nachricht Fehler: {e}")

    ################################################################################
    # BEFEHL: !ping
    ################################################################################
    @bot.command()
    async def ping(ctx):
        await ctx.send("🏓 Bot antwortet!")

    ################################################################################
    # BEFEHL: !info
    ################################################################################
    @bot.command(name="info")
    async def discord_info(ctx):
        await ctx.send(
            "📋 **Befehle**\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🚀 `!start` — Suche starten\n"
            "⏹️ `!stop` — Suche stoppen\n"
            "🔴 `!kill` — Bot beenden\n"
            "📊 `!status` — Live-Status\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "➕ `!new jordan 60` — Neue Suche\n"
            "🗑️ `!delete nike` — Kanal löschen\n"
            "🗑️ `!delete all` — Alles löschen"
        )

    ################################################################################
    # BEFEHL: !status
    ################################################################################
    @bot.command(name="status")
    async def discord_status(ctx):
        laufende_tasks = sum(1 for t in aktive_tasks if not t.done())
        gesamte_kanaele = len(discord_kanal_ids)
        
        # DB Status prüfen
        db_status = "🔴 Getrennt"
        db = _get_db()
        if db is not None:
            db_status = "🟢 Verbunden (Atlas)"

        suchbegriffe_anzahl = 0
        from glob import glob
        import json
        for datei in glob("queue_*.json"):
            try:
                with open(datei, "r", encoding="utf-8") as f:
                    q = json.load(f)
                    suchbegriffe_anzahl += len(q)
            except:
                pass
                
        status_msg = (
            f"📊 **Vinted Bot Status**\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🗄️ **Datenbank:** {db_status}\n"
            f"🟢 **Laufende Suchen:** {laufende_tasks}\n"
            f"📁 **Suchbegriffe:** {suchbegriffe_anzahl}\n"
            f"💬 **Discord Kanäle:** {gesamte_kanaele}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
        )
        if laufende_tasks > 0:
            status_msg += "✅ Suche ist aktiv!"
        else:
            status_msg += "⏸️ Bot ist im Standby."
            
        await ctx.send(status_msg)

    ################################################################################
    # BEFEHL: !stop  – alle Scraper-Prozesse stoppen
    ################################################################################
    @bot.command(name="stop")
    async def discord_stop(ctx):
        global aktive_tasks, discord_prozesse
        
        #1. Stoppen
        gestoppt = 0

        for t in aktive_tasks:
            if not t.done():
                t.cancel()
                gestoppt += 1
        aktive_tasks.clear()

        for p in discord_prozesse.values():
            if p.poll() is None:
                p.kill()
                gestoppt += 1
        discord_prozesse.clear()

        # 2. Queue-Dateien löschen
        geloeschte_dateien = 0
        for datei_pfad in glob("queue_*.json"):
            try:
                os.remove(datei_pfad)
                geloeschte_dateien += 1
            except Exception as e:
                print(f"⚠️ Konnte {datei_pfad} nicht löschen: {e}")

        if gestoppt > 0:
            await ctx.send(f"⏹️ Alle Suchen gestoppt.")
        else:
            await ctx.send("ℹ️ Es liefen keine aktiven Suchen.")

    ################################################################################
    # BEFEHL: !kill  – Bot komplett beenden (auch auf Render)
    ################################################################################
    @bot.command(name="kill")
    async def discord_kill(ctx):
        global aktive_tasks, discord_prozesse

        for t in aktive_tasks:
            if not t.done():
                t.cancel()
        aktive_tasks.clear()
        for p in discord_prozesse.values():
            if p.poll() is None:
                p.kill()
        discord_prozesse.clear()

        # 2. Queue-Dateien löschen
        geloeschte_dateien = 0
        for datei_pfad in glob("queue_*.json"):
            try:
                os.remove(datei_pfad)
                geloeschte_dateien += 1
            except Exception as e:
                print(f"⚠️ Konnte {datei_pfad} nicht löschen: {e}")

        await ctx.send("🔴 Bot wird jetzt beendet.")
        await bot.close()
        sys.exit(0)

    ################################################################################
    # BEFEHL: !delete all / !delete [name]
    ################################################################################
    @bot.command(name="delete")
    async def discord_delete(ctx, *, ziel=None):
        global aktive_tasks, discord_prozesse, discord_kanal_ids

        if not ziel:
            await ctx.send(
                "❌ Bitte angeben was gelöscht werden soll.\n"
                "`!delete all` oder `!delete [kanalname oder kategoriename]`"
            )
            return

        # ── !delete all ───────────────────────────────────────────────────────────
        if ziel.strip().lower() == "all":
            hauptkanal_id = int(DISCORD_CHANNEL_ID) if DISCORD_CHANNEL_ID else None

            # Erst alle Prozesse stoppen
            for t in aktive_tasks:
                if not t.done():
                    t.cancel()
            aktive_tasks.clear()
            for p in discord_prozesse.values():
                if p.poll() is None:
                    p.kill()
            discord_prozesse.clear()
            discord_kanal_ids.clear()

            geloescht_kanaele    = 0
            geloescht_kategorien = 0

            for channel in list(ctx.guild.text_channels):
                if channel.id == hauptkanal_id:
                    continue
                try:
                    await channel.delete()
                    geloescht_kanaele += 1
                except Exception as e:
                    print(f"⚠️ Kanal {channel.name} Fehler: {e}")

            for kategorie in list(ctx.guild.categories):
                try:
                    await kategorie.delete()
                    geloescht_kategorien += 1
                except Exception as e:
                    print(f"⚠️ Kategorie {kategorie.name} Fehler: {e}")

            # 3. MongoDB bereinigen
            db = _get_db()
            if db is not None:
                try:
                    await db["setup_struktur"].delete_many({})
                    await db["custom_searches"].delete_many({})
                    print("✅ MongoDB Suchen gelöscht.")
                except Exception as e:
                    print(f"⚠️ MongoDB Löschen Fehler: {e}")

            await ctx.send(
                f"🗑️ Aufgeräumt!\n"
                f"• {geloescht_kanaele} Kanäle gelöscht\n"
                f"• {geloescht_kategorien} Kategorien gelöscht\n"
                f"• Alle Suchen (auch in der DB) gestoppt"
            )
            return

        # ── !delete [name] – Kanal suchen ─────────────────────────────────────────
        name = ziel.strip().lower()

        gefundener_kanal = discord.utils.get(ctx.guild.text_channels, name=name)
        if gefundener_kanal:
            kanal_key = get_kanal_key(name)
            if kanal_key in discord_prozesse:
                discord_prozesse[kanal_key].kill()
                del discord_prozesse[kanal_key]
            if kanal_key in discord_kanal_ids:
                del discord_kanal_ids[kanal_key]
            # Aus MongoDB löschen
            db = _get_db()
            if db is not None:
                try:
                    # Lösche aus custom_searches (begriff oder channel_id)
                    await db["custom_searches"].delete_many({"$or": [
                        {"channel_name": name},
                        {"channel_id": str(gefundener_kanal.id)}
                    ]})
                    # Auch aus setup_struktur entfernen
                    await db["setup_struktur"].delete_many({"channel_id": str(gefundener_kanal.id)})
                except Exception as e:
                    print(f"⚠️ MongoDB Löschen Fehler: {e}")

            try:
                await gefundener_kanal.delete()
                await ctx.send(f"🗑️ Kanal **{name}** wurde gelöscht.")
            except Exception as e:
                await ctx.send(f"❌ Fehler beim Löschen: {e}")
            return

        # ── !delete [name] – Kategorie suchen ────────────────────────────────────
        gefundene_kategorie = None
        for kat in ctx.guild.categories:
            if kat.name.lower() == name or name in kat.name.lower():
                gefundene_kategorie = kat
                break

        if gefundene_kategorie:
            anzahl_kanaele = len(gefundene_kategorie.channels)
            for channel in list(gefundene_kategorie.channels):
                kanal_key = get_kanal_key(channel.name)
                if kanal_key in discord_prozesse:
                    discord_prozesse[kanal_key].kill()
                    del discord_prozesse[kanal_key]
                if kanal_key in discord_kanal_ids:
                    del discord_kanal_ids[kanal_key]
                try:
                    await channel.delete()
                except Exception:
                    pass
            try:
                await gefundene_kategorie.delete()
                await ctx.send(
                    f"🗑️ Kategorie **{gefundene_kategorie.name}** und "
                    f"{anzahl_kanaele} Kanal/Kanäle wurden gelöscht."
                )
            except Exception as e:
                await ctx.send(f"❌ Fehler beim Löschen: {e}")
            return

        await ctx.send(f"❌ Kein Kanal und keine Kategorie mit dem Namen **{name}** gefunden.")

    ################################################################################
    # BEFEHL: !new [suchbegriff] [maxpreis]
    # Erstellt einen Kanal in der Kategorie "Personal" und fügt ihn
    # zur kürzesten laufenden Queue hinzu.
    ################################################################################
    @bot.command(name="new")
    async def discord_new(ctx, *, eingabe=None):
        global discord_kanal_ids, aktive_prozess_anzahl

        if not eingabe:
            await ctx.send(
                "❌ Bitte Suchbegriff angeben.\n"
                "Beispiel: `!new jordan 60` oder `!new ralph lauren`"
            )
            return

        # Letztes Wort als Maxpreis interpretieren wenn es eine Zahl ist
        teile = eingabe.rsplit(" ", 1)
        if len(teile) == 2 and teile[1].replace(".", "").isdigit():
            suchbegriff = teile[0].strip()
            max_preis   = float(teile[1])
        else:
            suchbegriff = eingabe.strip()
            max_preis   = 0.0

        kanal_name = suchbegriff[:20].lower().replace(" ", "-")

        # Kategorie "Personal" suchen oder erstellen
        kategorie = discord.utils.get(ctx.guild.categories, name="Personal")
        if not kategorie:
            kategorie = await ctx.guild.create_category("Personal")

        # Kanal erstellen falls noch nicht vorhanden
        existiert = discord.utils.get(
            ctx.guild.text_channels,
            name=kanal_name,
            category=kategorie
        )
        if existiert:
            kanal = existiert
            await ctx.send(f"ℹ️ Der Kanal **{kanal_name}** existiert bereits in Personal.")
        else:
            kanal = await kategorie.create_text_channel(name=kanal_name)
            await ctx.send(f"✅ Kanal **{kanal_name}** wurde in **Personal** erstellt.")

        discord_kanal_ids[get_kanal_key(suchbegriff)] = kanal.id

        # In MongoDB speichern (bleibt nach Neustart erhalten)
        db = _get_db()
        if db is not None:
            try:
                await db["custom_searches"].update_one(
                    {"_id": suchbegriff},
                    {"$set": {
                        "channel_id": str(kanal.id),
                        "channel_name": kanal_name,
                        "kategorie": "Personal",
                        "begriff": suchbegriff,
                        "max_preis": max_preis,
                    }},
                    upsert=True
                )
            except Exception as e:
                print(f"⚠️ MongoDB custom_searches Fehler: {e}")

        # Zur kürzesten laufenden Queue hinzufügen
        laufende = [t for t in aktive_tasks if not t.done()]
        if not laufende:
            await ctx.send(
                f"⚠️ Keine aktive Suche läuft gerade.\n"
                f"Starte zuerst mit `!start`, dann wird **{suchbegriff}** automatisch mitgesucht."
            )
            return

        idx              = kuerzeste_queue_index()
        aktuelle_queue   = lade_queue(idx)
        aktuelle_queue.append({
            "channel_id": str(kanal.id),
            "begriff":    suchbegriff,
            "max_preis":  max_preis
        })
        await async_speichere_queue(idx, aktuelle_queue)

        preis_text = f" (max. {int(max_preis)}€)" if max_preis > 0 else ""
        await ctx.send(
            f"🔍 **{suchbegriff}**{preis_text} wurde zur Suche hinzugefügt.\n"
            f"Neue Artikel erscheinen in {kanal.mention}."
        )

    ################################################################################
    # BEFEHL: !start [anzahl_prozesse]
    # Startet die komplette Suche mit der vordefinierten Struktur.
    ################################################################################
    @bot.command(name="start")
    async def discord_start(ctx, anzahl_prozesse: int = 3):
        global aktive_tasks, discord_kanal_ids, aktive_prozess_anzahl

        # Limit: 1–10
        anzahl_prozesse = max(1, min(anzahl_prozesse, 10))

        await ctx.send("🚀 **Wird gestartet...** Kanäle werden aufgebaut.")

        # ── SETUP STRUKTUR ────────────────────────────────────────────────────────
        # Format pro Eintrag: ("kanalname", "suchbegriff", maxpreis_in_euro)
        SETUP_STRUKTUR = {
            "👑 Ralph Lauren": [
                ("rl-all",      "ralph lauren",                 40),
                ("rl-tshirts",  "ralph lauren t shirt",         20),
                ("rl-hoodies",  "ralph lauren hoodie pullover",  30),
                ("rl-polos",    "ralph lauren polo",             30),
                ("rl-jacken",   "ralph lauren jacke",            50),
            ],
            "👟 Nike": [
                ("nike-all",        "nike",             40),
                ("nike-hosen",      "nike hose",        25),
                ("nike-hoodies",    "nike hoodie",      30),
                ("nike-sneaker",    "nike sneaker",     50),
                ("nike-tracksuits", "nike tracksuit",   50),
            ],
            "🦆 Adidas": [
                ("adidas-all",        "adidas",           40),
                ("adidas-hosen",      "adidas hose",      25),
                ("adidas-hoodies",    "adidas hoodie",    30),
                ("adidas-tracksuits", "adidas tracksuit", 50),
            ],
            "🔥 Andere Marken": [
                ("corteiz",       "corteiz",          40),
                ("stone-island",  "stone island",     40),
                ("lacoste",       "lacoste",          30),
                ("stussy",        "stussy",           40),
                ("carhartt",      "carhartt",         30),
                ("jacken-all",    "jacke ralph lauren nike adidas carhartt", 80),
            ],
            "👖 Jeans": [
                ("dg-jeans",     "dolce gabbana jeans",  70),
                ("missme-jeans", "miss me jeans",         50),
                ("levis-jeans",  "levis jeans",           30),
                ("tr-jeans",     "true religion jeans",   70),
            ],
            "👟 Sneaker": [
                ("sneaker-all", "sneaker",  40),
                ("jordans",     "jordan",   60),
                ("dunks",       "dunk",     50),
            ],
            "💻 Tech": [
                ("gaming-pc",  "gaming pc",    450),
                ("pc-parts",   "gpu ram",      200),
            ],
        }

        gesamt_neu       = 0
        gesamt_existiert = 0
        alle_eintraege   = []

        # ── Schritt 0: Gespeicherte Custom-Searches aus MongoDB laden ──────────────
        db = _get_db()
        if db is not None:
            try:
                cursor = db["custom_searches"].find({})
                customs = await cursor.to_list(length=1000)
                for c in customs:
                    # Prüfen ob der Kanal noch existiert
                    kanal = bot.get_channel(int(c["channel_id"]))
                    if kanal:
                        alle_eintraege.append({
                            "channel_id": c["channel_id"],
                            "begriff":    c["begriff"],
                            "max_preis":  c["max_preis"],
                            "kanal_name": c.get("channel_name", ""),
                            "kategorie":  c.get("kategorie", "Personal")
                        })
                        discord_kanal_ids[get_kanal_key(c["begriff"])] = kanal.id
                if customs:
                    await ctx.send(f"♻️ {len(customs)} gespeicherte Suchen aus der Datenbank geladen.")
            except Exception as e:
                print(f"⚠️ MongoDB Load Error: {e}")

        # ── Schritt 1: Kategorien und Kanäle erstellen ────────────────────────────
        for kategorie_name, kanaele in SETUP_STRUKTUR.items():
            kategorie = discord.utils.get(ctx.guild.categories, name=kategorie_name)
            if not kategorie:
                kategorie = await ctx.guild.create_category(kategorie_name)

            for kanal_name, suchbegriff, max_preis in kanaele:
                existiert = discord.utils.get(
                    ctx.guild.text_channels,
                    name=kanal_name,
                    category=kategorie
                )
                if existiert:
                    kanal = existiert
                    gesamt_existiert += 1
                else:
                    kanal = await kategorie.create_text_channel(name=kanal_name)
                    gesamt_neu += 1

                discord_kanal_ids[get_kanal_key(suchbegriff)] = kanal.id
                alle_eintraege.append({
                    "channel_id": str(kanal.id),
                    "begriff":    suchbegriff,
                    "max_preis":  max_preis,
                    "kanal_name": kanal_name,
                    "kategorie":  kategorie_name,
                })

        await ctx.send(
            f"✅ Kanäle bereit: {gesamt_neu} neu erstellt, {gesamt_existiert} bereits vorhanden."
        )

        # ── Gesamte Struktur in MongoDB sichern ──────────────────────────────────
        db = _get_db()
        if db is not None:
            try:
                await db["setup_struktur"].delete_many({})
                if alle_eintraege:
                    await db["setup_struktur"].insert_many(alle_eintraege)
                print(f"✅ {len(alle_eintraege)} Sucheinträge in MongoDB gespeichert.")
            except Exception as e:
                print(f"⚠️ MongoDB setup_struktur Fehler: {e}")

        # ── Schritt 2: Alte Prozesse stoppen ─────────────────────────────────────
        gestoppt = 0
        for t in aktive_tasks:
            if not t.done():
                t.cancel()
                gestoppt += 1
        aktive_tasks.clear()
        if gestoppt:
            await ctx.send(f"⏹️ {gestoppt} alte Suchen gestoppt.")

        # ── Schritt 3: Queue-Daten schreiben (MongoDB + Fallback) ─────────────────
        queues = verteile_auf_queues(alle_eintraege, anzahl_prozesse)
        for i, eintraege in enumerate(queues):
            await async_speichere_queue(i, eintraege)

        aktive_prozess_anzahl = anzahl_prozesse

        # ── Schritt 4: Prozesse starten ───────────────────────────────────────────
        for i in range(anzahl_prozesse):
            t = bot.loop.create_task(
                starte_queue_async(QUEUE_FILE.format(i))
            )
            aktive_tasks.append(t)

        pro_prozess = math.ceil(len(alle_eintraege) / anzahl_prozesse)
        await ctx.send(
            f"✅ **Suche läuft!**\n"
            f"• {len(alle_eintraege)} Suchbegriffe werden überwacht\n"
            f"• {anzahl_prozesse} parallele Prozesse ({pro_prozess} Begriffe pro Prozess)\n\n"
            f"`!stop` → alle Suchen stoppen\n"
            f"`!new [begriff] [maxpreis]` → neue Suche hinzufügen"
        )

    ################################################################################
    # MAIN - Bot starten
    ################################################################################
    async def main():
        keep_alive()
        async with bot:
            await bot.start(TOKENDISCORD)

    asyncio.run(main())

################################################################################
# FEHLERBEHANDLUNG
################################################################################
except Exception as e:
    print("Programm beendet ✅", e)
