################################################################################
#                                                                              #
#  🤖 VINTED SCRAPER BOT - HAUPTDATEI (main.py)                               #
#                                                                              #
#  Diese Datei ist das GEHIRN des Projekts!                                   #
#  Sie startet BEIDE Bots gleichzeitig (Discord + Telegram)                   #
#  und verwaltet alle Befehle die der Benutzer schreiben kann.                #
#                                                                              #
#  KURZ: main.py = Kontrollzentrale des gesamten Bots                         #
#                                                                              #
################################################################################

import sys
sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)  # UTF-8 + sofortige Ausgabe
sys.stderr.reconfigure(encoding='utf-8')  # Auch Fehler in UTF-8

try:
    ################################################################################
    # IMPORTS - Alles was wir brauchen
    ################################################################################
    # pyfiglet: Erstellt großen Text-Banner (für cooleres Aussehen)
    from pyfiglet import figlet_format

    #damit der docker/render server nicht einschläft
    from keep_alive import keep_alive
    
    # Telegram-Bibliothek: Für den Telegram-Bot
    from telegram import Update
    from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
    
    # Discord-Bibliothek: Für den Discord-Bot
    import discord
    from discord.ext import commands
    
    # Umgebungsvariablen laden (für Tokens aus .env)
    from dotenv import load_dotenv
    
    # Standard Python Bibliotheken
    import asyncio  # Für gleichzeitige Prozesse
    import os       # Für Umgebungsvariablen
    import subprocess  # Für Hintergrund-Prozesse starten
    import json     # Für JSON-Datei verarbeitung
    import re       # Für HTML-Tags entfernen (Konsolen-Ausgabe)
    
    # Unsere eigenen Dateien
    from config import TOKEN, Chat_ID          # Telegram Token und Chat ID
    from data_telegram import log_suche        # Logging-Funktion
    
    # HTTP-Requests für Vinted-API
    import requests
    
    ################################################################################
    # BANNER & SETUP - Die Begrüßung
    ################################################################################
    banner = figlet_format("Vinted X Discord Bot", font="small")
    print(banner, "\nmade by python_tutorials_de\n")
    
    ################################################################################
    # GLOBALE VARIABLEN - Speicher für laufende Prozesse
    ################################################################################
    # Diese Variablen speichern die laufenden Scraper-Prozesse
    # Damit können wir sie später stoppen (mit !stop Befehl)

    ################################################################################
    # GLOBALE PROZESS-VARIABLEN
    ################################################################################
    logprozess = None                    # Für das Dashboard (optional)
    prozess = None                       # Der Telegram Scraper Prozess
    discord_prozesse = {}                # Dict mit laufenden Discord Scraper Prozessen {"nike": prozess, "adidas": prozess}
    discord_kanal_ids = {}               # Dict für Zuordnung {"nike": channel_id, "adidas": channel_id}
    SEEN_FILE = "seen.json"              # Datei mit Artikel die wir schon gesehen haben

    ################################################################################
    # HELPER FUNKTION: get_kanal_key()
    ################################################################################
    def get_kanal_key(suchbegriff):
        """Erstelle einen konsistenten Schlüssel aus dem Suchbegriff (gekürzt auf 20 Zeichen, lowercase)"""
        return suchbegriff[:20].lower()

    ################################################################################
    # OPTIONAL: Dashboard starten - VOR den Scrapern!
    ################################################################################
    # Dashboard muss ZUERST starten damit JSON-Dateien geleert werden
    #print("\n🚀 Starte Dashboard...")
    #logprozess = subprocess.Popen(["python", "dashboard.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print("✅ Dashboard verfügbar aber nicht geöffnet wegen Serverversion!\n")
    
    import time
    time.sleep(2)  # Warte bis Dashboard JSON-Dateien geleert hat
    
    ################################################################################
    # UMGEBUNGSVARIABLEN LADEN
    ################################################################################
    # .env Datei laden (mit deine Tokens)
    load_dotenv()
    load_dotenv(".env", override=True)  # Explizit nach .env suchen
    
    # Discord Token laden
    TOKENDISCORD = os.getenv("DISCORD_TOKEN")
    DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
    
    # ✅ FEHLERPRÜFUNG
    print("\n" + "="*50)
    print("🔍 Token-Status:")
    print("="*50)
    print(f"✅ Telegram Token: {bool(TOKEN)}")
    print(f"✅ Discord Token: {bool(TOKENDISCORD)}")
    print(f"✅ Discord Channel: {bool(DISCORD_CHANNEL_ID)}")
    print("="*50 + "\n")
    
    def env_token_speichern(key: str, wert: str):
        """Schreibe oder überschreibe einen Key in der .env Datei"""
        env_path = ".env"
        lines = []
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError:
            pass
    
        # Bestehende Zeile ersetzen oder neue anhängen
        key_gefunden = False
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={wert}\n"
                key_gefunden = True
                break
        if not key_gefunden:
            lines.append(f"{key}={wert}\n")
    
        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(lines)

    def env_token_loeschen(key: str):
        """Entferne einen Key aus der .env Datei"""
        env_path = ".env"
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(line for line in lines if not line.startswith(f"{key}="))
        except FileNotFoundError:
            pass

    if not TOKENDISCORD:
        print("⚠️ DISCORD_TOKEN fehlt in der .env!")
        print("👉 Du kannst ihn jetzt eingeben (oder Enter zum Überspringen):")
        eingabe = input("DISCORD_TOKEN: ").strip()
    
        if eingabe:
            env_token_speichern("DISCORD_TOKEN", eingabe)
            os.environ["DISCORD_TOKEN"] = eingabe
            TOKENDISCORD = eingabe
            print("✅ Token gespeichert! Teste Verbindung...")
        
            # Token testen
            import requests as req
            test = req.get(
                "https://discord.com/api/v10/users/@me",
                headers={"Authorization": f"Bot {TOKENDISCORD}"},
                timeout=10
            )
            if test.status_code != 200:
                print(f"❌ Token ungültig (Status {test.status_code})! Wird aus .env gelöscht.")
                env_token_loeschen("DISCORD_TOKEN")
                sys.exit(1)
            else:
                print("✅ Discord Token funktioniert!")
        else:
            print("❌ Kein Token eingegeben. Beende.")
            sys.exit(1)

    if not TOKEN:
        print("⚠️ TELEGRAM_TOKEN fehlt in der .env!")
        print("👉 Du kannst ihn jetzt eingeben (oder Enter zum Überspringen):")
        eingabe = input("TELEGRAM_TOKEN: ").strip()
    
        if eingabe:
            env_token_speichern("TELEGRAM_TOKEN", eingabe)
            os.environ["TELEGRAM_TOKEN"] = eingabe
            TOKEN = eingabe
            print("✅ Telegram Token gespeichert!")
        else:
            print("❌ Kein Token eingegeben. Beende.")
            sys.exit(1)

    ################################################################################
    # DISCORD BOT SETUP - Der Discord-Teil
    ################################################################################
    # Hier bauen wir den Discord-Bot zusammen
    # "Intents" = Was der Bot alles lesen darf
    
    intents = discord.Intents.default()           # Standard Berechtigungen
    intents.message_content = True                # Bot darf Nachrichten-Inhalt lesen
    bot = commands.Bot(command_prefix="!", intents=intents)  # ! = Befehl-Präfix (z.B. !start)

    ################################################################################
    # DISCORD EVENT: on_ready - Wenn Bot online geht
    ################################################################################
    @bot.event
    async def on_ready():
        """Diese Funktion wird ausgeführt, wenn der Discord Bot sich online gemeldet hat"""
        print(f'✅ Discord Bot eingeloggt als {bot.user}')
        
        # Versuche eine Start-Nachricht im Discord-Channel zu senden
        channel_id_str = os.getenv("DISCORD_CHANNEL_ID")  # Channel ID aus .env
        
        if channel_id_str:
            try:
                channel_id = int(channel_id_str)  # Text zu Nummer umwandeln
                channel = bot.get_channel(channel_id)  # Finde den Channel
                
                if channel:
                    # Nachricht die angezeigt wird, wenn Bot startet
                    discord_startup_msg = """🚀 **Vinted Scraper Bot online!**

Der Bot wurde erfolgreich gestartet und ist einsatzbereit.
Dieser Bot wurde von **python_tutorials_de** erstellt.

📋 **Discord Commands:**
💡 `!id` → Deine Discord ID
🆕 `!new [Begriff]` → Neuer Kanal mit Scraper
🔄 `!start [Begriff]` → Kontinuierliche Überwachung im aktuellen Channel
🔍 `!suche [Begriff]` → Einmalige Schnellsuche
⏹️ `!stop [Begriff]` → Scraper stoppen
🗑️ `!delete [Begriff]` → Kanal löschen
📋 `!channels` → Alle aktiven Kanäle anzeigen
ℹ️ `!info` → Alle verfügbaren Befehle anzeigen
ℹ️ `!setup` → Gewünschtes Setup für den Server mit allen Filtern und Scrapern

✨ **Features:**
✅ Echtzeit-Benachrichtigungen
📸 Mit Produktfotos
💰 Preisanzeige
🔗 Direkte Vinted-Links"""
                    await channel.send(discord_startup_msg)
                    print(f"✅ Discord Start-Nachricht an Kanal {channel_id} gesendet.")
                else:
                    print("❌ Discord Channel nicht gefunden! Hat der Bot Zugriff auf diesen Kanal?")
            except ValueError:
                print("❌ Die DISCORD_CHANNEL_ID in der .env muss eine Zahl sein!")
        else:
            print("⚠️ Keine DISCORD_CHANNEL_ID in der .env gefunden. Start-Nachricht wird übersprungen.")

    ################################################################################
    # DISCORD BEFEHL: !ping - Test ob Bot reagiert
    ################################################################################
    @bot.command()
    async def ping(ctx):
        """Einfacher Test-Befehl"""
        await ctx.send("Pong! 🏓")


    ################################################################################
    # DISCORD BEFEHL: !id - Zeige meine ID
    ################################################################################
    @bot.command(name="id")
    async def discord_id(ctx):
        """Zeige die Discord User ID und Channel ID an"""
        await ctx.send(f"💡 Deine Discord User ID: `{ctx.author.id}`\n📌 Channel ID: `{ctx.channel.id}`")
        print(f"Discord ID abgerufen: {ctx.author.id}")

    #Starte einen neuen Scraper in einem neuen kanal mit festem Suchbegriff
    @bot.command(name="new")
    async def discord_new(ctx, *, begriff=None):
        global discord_prozesse, discord_kanal_ids

        if not begriff:
            await ctx.send("❌ Bitte Suchbegriff angeben!")
            return
        
        # Erstelle einen konsistenten Schlüssel
        kanal_key = get_kanal_key(begriff)
        kanal_name = f"vinted-{kanal_key}"
        existierender_kanal = discord.utils.get(ctx.guild.channels, name=kanal_name)
        
        try:
            # Wenn Kanal bereits existiert, nutze ihn
            if existierender_kanal:
                await ctx.send(f"ℹ️ Kanal `{kanal_name}` existiert bereits!")
                kanal_id = existierender_kanal.id
                await ctx.send(f"🔍 Starte Scraper für: `{begriff}`")
            else:
                # Erstelle neuen Kanal wenn er nicht existiert
                await ctx.send(f"🚀 Starte neuen Kanal für: `{kanal_name}`")
                existierender_kanal = await ctx.guild.create_text_channel(name=kanal_name)
                kanal_id = existierender_kanal.id
                print(f"Neuer Kanal erstellt: {existierender_kanal.name} (ID: {kanal_id})")
                await ctx.send(f"✅ Neuer Kanal erstellt: `{existierender_kanal.name}`")
                await ctx.send(f"🔍 Starte Scraper für: `{begriff}`")
            
            # Stoppe alten Scraper falls vorhanden
            if kanal_key in discord_prozesse:
                discord_prozesse[kanal_key].kill()
                del discord_prozesse[kanal_key]
                await ctx.send(f"⏸️ Alter Scraper gestoppt")
            
            # Starte neuen Scraper
            await ctx.send(f"🚀 Vinted Scraper gestartet!")
            await ctx.send(f"🔍 Suchbegriff: `{begriff}`\n⏱️ Läuft kontinuierlich...\n📲 Du erhältst Benachrichtigungen im Channel: `{existierender_kanal.name}`")
            print(f"🚀 Discord Scraper gestartet: {begriff} im Kanal: {existierender_kanal.name}")

            # Starte data_discord.py als separaten Prozess im Hintergrund
            prozess = subprocess.Popen(["python", "data_discord.py", str(kanal_id), begriff])
            discord_prozesse[kanal_key] = prozess
            discord_kanal_ids[kanal_key] = kanal_id
        except Exception as e:
            await ctx.send(f"❌ Fehler: {str(e)}")
            print(f"Fehler in discord_new: {e}")

    ################################################################################
    # DISCORD BEFEHL: !start [Begriff] - Starte kontinuierlichen Scraper
    ################################################################################
    @bot.command(name="start")
    async def discord_start(ctx, *, begriff=None):
        """
        Starte einen neuen Vinted-Scraper mit einem Suchbegriff
        Beispiel: !start Nike Turnschuhe
        """
        global discord_prozesse
        
        # Fehlerbehandlung: Suchbegriff vorhanden?
        if not begriff:
            await ctx.send("❌ Bitte Suchbegriff angeben!\n\n📝 Beispiel: `!start nike`")
            return

        # Erstelle konsistenten Schlüssel
        kanal_key = get_kanal_key(begriff)
        
        # Falls bereits dieser Scraper läuft, stoppe ihn
        if kanal_key in discord_prozesse:
            discord_prozesse[kanal_key].kill()
            del discord_prozesse[kanal_key]
            print(f"Alter Scraper für {kanal_key} gestoppt ✅")

        # Nachrichten senden
        await ctx.send(f"✅ Vinted Scraper gestartet!")
        await ctx.send(f"🔍 Suchbegriff: `{begriff}`\n⏱️ Läuft kontinuierlich...\n📲 Du erhältst Benachrichtigungen hier im Channel!")
        print(f"🚀 Discord Scraper gestartet: {begriff}")
        
        # Starte data_discord.py als separaten Prozess im Hintergrund
        # Übergebe: Channel-ID und Suchbegriff als Argumente
        prozess = subprocess.Popen(["python", "data_discord.py", str(ctx.channel.id), begriff])
        discord_prozesse[kanal_key] = prozess

    ################################################################################
    # DISCORD BEFEHL: !stop - Stoppe einen spezifischen Scraper
    ################################################################################
    @bot.command(name="stop")
    async def discord_stop(ctx, *, begriff=None):
        """Stoppe einen laufenden Scraper
        Beispiel: !stop nike
        """
        global discord_prozesse
        
        if not begriff:
            await ctx.send("❌ Bitte Suchbegriff angeben!\n\n📝 Beispiel: `!stop nike`")
            return
        
        kanal_key = get_kanal_key(begriff)
        
        if kanal_key in discord_prozesse:
            discord_prozesse[kanal_key].kill()
            del discord_prozesse[kanal_key]
            if kanal_key in discord_kanal_ids:
                del discord_kanal_ids[kanal_key]
            await ctx.send(f"⏹️ Scraper für `{begriff}` gestoppt!\n💤 Keine neuen Benachrichtigungen mehr.")
            print(f"⏹️ Discord Scraper für {kanal_key} gestoppt")
        else:
            await ctx.send(f"⚠️ Kein aktiver Scraper für `{begriff}` läuft!")

    ################################################################################
    # DISCORD BEFEHL: !delete [Begriff] - Lösche einen Kanal
    ################################################################################
    @bot.command(name="delete")
    async def discord_delete(ctx, *, begriff=None):
        """Lösche einen Vinted-Kanal und stoppe den Scraper
        Beispiel: !delete nike
        """
        global discord_prozesse, discord_kanal_ids
        
        if not begriff:
            await ctx.send("❌ Bitte Suchbegriff angeben!\n\n📝 Beispiel: `!delete nike`")
            return
        
        kanal_key = get_kanal_key(begriff)
        kanal_name = f"vinted-{kanal_key}"
        kanal = discord.utils.get(ctx.guild.channels, name=kanal_name)
        
        if not kanal:
            await ctx.send(f"❌ Kanal `{kanal_name}` nicht gefunden!")
            return
        
        try:
            # Prüfe ob ein Scraper läuft und stoppe ihn
            scraper_war_aktiv = False
            if kanal_key in discord_prozesse:
                discord_prozesse[kanal_key].kill()
                del discord_prozesse[kanal_key]
                scraper_war_aktiv = True
                print(f"Scraper für {kanal_key} gestoppt")
            
            if kanal_key in discord_kanal_ids:
                del discord_kanal_ids[kanal_key]
            
            # Lösche den Kanal
            await kanal.delete()
            
            # Unterschiedliche Nachricht je nachdem ob Scraper aktiv war
            if scraper_war_aktiv:
                await ctx.send(f"✅ Kanal `{kanal_name}` gelöscht und Scraper gestoppt!")
                print(f"Kanal {kanal_name} gelöscht und aktiver Scraper beendet")
            else:
                await ctx.send(f"✅ Kanal `{kanal_name}` gelöscht!")
                print(f"Kanal {kanal_name} gelöscht (kein Scraper war aktiv)")
        except Exception as e:
            await ctx.send(f"❌ Fehler beim Löschen: {str(e)}")
            print(f"Fehler in discord_delete: {e}")

    ################################################################################
    # DISCORD BEFEHL: !channels - Zeige alle laufenden Kanäle
    ################################################################################
    ################################################################################
    # DISCORD BEFEHL: !channels - Zeige ABSOLUT ALLE Kanäle
    ################################################################################
    @bot.command(name="channels")
    async def discord_channels(ctx):
        """Listet alle aktiven Scraper und alle verfügbaren Such-Kanäle auf."""
        global discord_prozesse, discord_kanal_ids
        
        msg = "📋 **Vinted Scraper Gesamt-Übersicht**\n"
        msg += "---" * 5 + "\n\n"
        
        # 1. Teil: Was läuft GERADE? (Live aus dem Speicher)
        msg += "🟢 **AKTIVE LIVE-SCRAPER:**\n"
        if not discord_prozesse:
            msg += "*Aktuell laufen keine Hintergrund-Prozesse.*\n"
        else:
            for key in discord_prozesse.keys():
                k_id = discord_kanal_ids.get(key)
                # Suche den Kanal serverweit (auch in Kategorien)
                kanal_obj = bot.get_channel(k_id) 
                k_mention = kanal_obj.mention if kanal_obj else f"`#{key}`"
                msg += f"• `{key}` ➜ aktiv in {k_mention}\n"
        
        msg += "\n"

        # 2. Teil: Welche Kanäle existieren insgesamt für die Suche?
        # Wir gehen durch ALLE Textkanäle des Servers
        msg += "📂 **VERFÜGBARE SUCH-KANÄLE (Serverweit):**\n"
        
        gefundene_kanale = []
        for channel in ctx.guild.text_channels:
            # Wir nehmen alle, die entweder mit 'vinted-' starten 
            # ODER die wir in unseren Setup-Listen haben
            is_setup_channel = any(key in channel.name for key in discord_prozesse.keys())
            
            if channel.name.startswith("vinted-") or is_setup_channel:
                status = "✅" if channel.id in discord_kanal_ids.values() else "💤"
                kat_name = f"[{channel.category.name}]" if channel.category else "[Keine Kat.]"
                gefundene_kanale.append(f"• {status} {kat_name} {channel.mention}")

        if not gefundene_kanale:
            msg += "*Keine speziellen Such-Kanäle gefunden.*\n"
        else:
            # Wir sortieren sie nach Kategorien für bessere Übersicht
            msg += "\n".join(sorted(gefundene_kanale))

        msg += "\n\n*Legende: 🟢/✅ = Läuft | 💤 = Gestoppt*"
        
        # Falls die Nachricht zu lang wird (Discord Limit 2000 Zeichen)
        if len(msg) > 2000:
            await ctx.send(msg[:1990] + "...")
        else:
            await ctx.send(msg)

    ################################################################################
    # DISCORD BEFEHL: !info - Zeige Informationen
    ################################################################################
    @bot.command(name="info")
    async def discord_info(ctx):
        """Zeige eine Hilfenachricht mit allen Befehlen"""
        info_msg = """ℹ️ **Vinted Scraper Bot - Informationen**

🤖 Dieser Bot wurde von **python_tutorials_de** erstellt.
Er durchsucht Vinted nach neuen Artikeln und sendet dir automatisch Benachrichtigungen!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 **Discord Commands:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 `!id` → Zeige deine Discord ID an
🆕 `!new [Begriff]` → Erstelle neuen Kanal + starte Scraper
🔄 `!start [Begriff]` → Starte Scraper im aktuellen Channel
🔍 `!suche [Begriff]` → Einmalige Schnellsuche (nicht kontinuierlich)
⏹️ `!stop [Begriff]` → Stoppe einen laufenden Scraper
🗑️ `!delete [Begriff]` → Lösche Kanal + stoppe Scraper
📋 `!channels` → Zeige alle aktiven Kanäle & IDs
ℹ️ `!info` → Diese Nachricht

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ **Features:**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Echtzeitbenachrichtigungen für neue Artikel
📸 Produktfoto automatisch mitgesendet
💰 Preisanzeige in EUR
🔗 Direkter Link zum Artikel auf Vinted
🔄 Mehrere Scraper gleichzeitig möglich

💡 **Tip:** Nutze `!new` um separate Kanäle für verschiedene Suchbegriffe zu erstellen!"""
        await ctx.send(info_msg)

    ################################################################################
    # DISCORD BEFEHL: !setup - Erstellt vordefinierte Kategorien und Kanäle
    ################################################################################
    @bot.command(name="setup")
    async def discord_setup(ctx):
        """
        Erstellt vordefinierte Kategorien und Kanäle beim ersten Start.
        Prüft welche bereits existieren und erstellt nur die fehlenden.
        Startet danach automatisch Scraper für alle Kanäle.
    
        Beispiel: !setup
        """
        global discord_prozesse, discord_kanal_ids

        # ── KONFIGURATION: Hier Kategorien und Kanäle definieren ──────────────────
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
        # ──────────────────────────────────────────────────────────────────────────

        await ctx.send("🚀 **Setup gestartet!** Prüfe Kategorien und Kanäle...")

        gesamt_neu = 0
        gesamt_existiert = 0
        gestartete_scraper = []

        for kategorie_name, kanaele in SETUP_STRUKTUR.items():

            # ── Kategorie prüfen / erstellen ──────────────────────────────────────
            kategorie = discord.utils.get(ctx.guild.categories, name=kategorie_name)
            if kategorie:
                await ctx.send(f"✅ Kategorie **{kategorie_name}** existiert bereits.")
            else:
                kategorie = await ctx.guild.create_category(kategorie_name)
                await ctx.send(f"🆕 Kategorie **{kategorie_name}** erstellt.")

            # ── Kanäle in der Kategorie prüfen / erstellen ────────────────────────
            for kanal_name, suchbegriff, max_preis in kanaele:

                # Prüfe ob Kanal bereits in dieser Kategorie existiert
                existiert = discord.utils.get(
                    ctx.guild.text_channels,
                    name=kanal_name,
                    category=kategorie
                )

                if existiert:
                    kanal = existiert
                    await ctx.send(f"  ↳ ✅ `{kanal_name}` existiert bereits.")
                    gesamt_existiert += 1
                else:
                    kanal = await kategorie.create_text_channel(name=kanal_name)
                    await ctx.send(f"  ↳ 🆕 `{kanal_name}` erstellt.")
                    gesamt_neu += 1

                # ── Scraper starten falls noch nicht läuft ────────────────────────
                kanal_key = get_kanal_key(suchbegriff)

                if kanal_key in discord_prozesse:
                    # Alter Scraper läuft schon → überspringen
                    await ctx.send(f"  ↳ ⏩ Scraper für `{suchbegriff}` läuft bereits.")
                else:
                    prozess = subprocess.Popen(
                        ["python", "data_discord.py", str(kanal.id), suchbegriff, str(max_preis)]
                    )
                    discord_prozesse[kanal_key] = prozess
                    discord_kanal_ids[kanal_key] = kanal.id
                    gestartete_scraper.append(suchbegriff)
                    await ctx.send(f"  ↳ 🤖 Scraper gestartet: `{suchbegriff}` (max. {max_preis}€)")


        # ── Zusammenfassung ───────────────────────────────────────────────────────
        await ctx.send(
            f"\n✅ **Setup abgeschlossen!**\n"
            f"📁 Neue Kanäle erstellt: `{gesamt_neu}`\n"
            f"♻️ Bereits vorhanden: `{gesamt_existiert}`\n"
            f"🤖 Scraper gestartet: `{len(gestartete_scraper)}`\n"
            f"🔍 Aktive Suchen: {', '.join(f'`{s}`' for s in gestartete_scraper) if gestartete_scraper else 'keine neuen'}"
        )


    ################################################################################
    # DISCORD BEFEHL: !suche [Begriff] - Einmalige Schnellsuche
    ################################################################################
    @bot.command(name="suche")
    async def discord_suche(ctx, *, begriff=None):
        """Mach eine schnelle einmalige Suche (nicht kontinuierlich)"""
        if not begriff:
            await ctx.send("❌ Bitte Suchbegriff angeben!\n\n📝 Beispiel: `!suche nike`")
            return

        await ctx.send(f"🔍 Einmalige Schnellsuche für: `{begriff}`...")
        log_suche(begriff)

        try:
            # Erstelle eine neue HTTP Session
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "de-DE,de;q=0.9",
                "Referer": "https://www.vinted.de/",
            })
            # Hole Cookie von Vinted
            session.get("https://www.vinted.de", timeout=10)

            # Mache API-Request zu Vinted
            url = "https://www.vinted.de/api/v2/catalog/items"
            params = {
                "search_text": begriff,
                "order": "newest_first",
                "per_page": 10,
                "page": 1,
                "country_ids": ",".join(str(i) for i in range(1, 33)),
            }

            response = session.get(url, params=params, timeout=10)
            response.raise_for_status()
            artikel = response.json().get("items", [])

            # Falls Artikel gefunden, schreibe sie
            if artikel:
                await ctx.send(f"✨ **{len(artikel)} aktuelle Artikel gefunden!**")
                for a in artikel:
                    # Preis formatieren
                    preis = a.get('price', {})
                    if isinstance(preis, dict):
                        preis_text = f"{preis.get('amount', 'N/A')} {preis.get('currency_code', 'EUR')}"
                    else:
                        preis_text = f"{preis} EUR"

                    link = f"https://www.vinted.de/items/{a['id']}"
                    foto = ""
                    if a.get("photo") and a["photo"].get("url"):
                        foto = a["photo"]["url"]

                    nachricht = (
                        f"📦 **{a['title']}**\n"
                        f"💶 {preis_text}\n"
                        f"🔗 {link}"
                    )

                    # Mit Bild oder ohne?
                    if foto:
                        embed = discord.Embed(description=nachricht, color=0x00b4d8)
                        embed.set_image(url=foto)
                        await ctx.send(embed=embed)
                    else:
                        await ctx.send(nachricht)

                await ctx.send("✅ Schnellsuche abgeschlossen!")
            else:
                await ctx.send(f"🔍 Keine Artikel gefunden für: `{begriff}`")

        except Exception as e:
            await ctx.send(f"⚠️ Fehler bei der Suche:\n❌ {str(e)}")
            print(f"Discord Suche Fehler: {e}")

    ################################################################################
    # TELEGRAM BOT SETUP - Der Telegram-Teil
    ################################################################################
    # Telegram-Bot Funktion funktioniert sehr ähnlich wie Discord
    
    startup_msg = """🚀 Telegram-Vinted-Bot online!

Der Bot wurde erfolgreich gestartet und ist einsatzbereit.
Dieser Bot wurde von python_tutorials_de erstellt.

📋 Telegram Commands:
💡 /id → Deine Chat ID anzeigen
🔄 /start [Begriff] → Kontinuierliche Vinted-Suche starten
🔍 /suche [Begriff] → Einmalige Schnellsuche
⏹️ /stop → Scraper stoppen
ℹ️ /info → Alle verfügbaren Befehle anzeigen

✨ Features:
✅ Echtzeit-Benachrichtigungen
📸 Mit Produktfotos
💰 Preisanzeige
🔗 Direkte Vinted-Links"""

    ################################################################################
    # TELEGRAM HOOKS - Funktionen die beim Starten/Stoppen laufen
    ################################################################################
    async def on_start_hook(app):
        """Wird ausgeführt wenn Telegram-Bot startet"""
        await app.bot.send_message(chat_id=Chat_ID, text=startup_msg)
        print(startup_msg)
        print(f"Chat ID: {Chat_ID} 💡")

    async def on_shutdown_hook(app):
        """Wird ausgeführt wenn Telegram-Bot stoppt"""
        await app.bot.send_message(chat_id=Chat_ID, text="Bot wird jetzt beendet. 👋")

    # Telegram Application bauen
    app = ApplicationBuilder().token(TOKEN).post_init(on_start_hook).post_shutdown(on_shutdown_hook).build()

    ################################################################################
    # TELEGRAM BEFEHL: /id - Zeige deine Chat ID
    ################################################################################
    async def tg_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Zeige die Telegram Chat ID an"""
        chat_id = update.message.chat_id
        await update.message.reply_text(f"Deine Chat ID ist: {chat_id} 💡")

    ################################################################################
    # TELEGRAM BEFEHL: /start [Begriff] - Starte kontinuierlichen Scraper
    ################################################################################
    async def tg_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Starte einen Scraper mit Suchbegriff"""
        global prozess
        
        # Fehlerbehandlung
        if not context.args:
            await update.message.reply_text("❌ Bitte Suchbegriff angeben!\n\n📝 Beispiel: /start nike")
            return
        
        # Kombiniere alle Worte des Suchbegriffs
        neuer_begriff = " ".join(context.args)
        
        # Stoppe alte Scraper
        if prozess:
            prozess.kill()
        
        # Sende bestätigungsnachrichten
        await update.message.reply_text("✅ Vinted Scraper gestartet!")
        await update.message.reply_text(f"🔍 Suchbegriff: '{neuer_begriff}'\n⏱️ Läuft kontinuierlich...\n📲 Du erhältst Benachrichtigungen!")
        
        # Starte data_telegram.py im Hintergrund
        chat_id = str(update.message.chat_id)
        prozess = subprocess.Popen(["python", "data_telegram.py", chat_id, neuer_begriff])
        
    ################################################################################
    # TELEGRAM BEFEHL: /stop - Stoppe Scraper
    ################################################################################
    async def tg_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Stoppe den laufenden Scraper"""
        global prozess
        if prozess:
            prozess.kill()
            prozess = None
            await update.message.reply_text("⏹️ Vinted Scraper gestoppt!\n💤 Keine neuen Benachrichtigungen mehr.")
        else:
            await update.message.reply_text("⚠️ Kein aktiver Scraper läuft!")

    ################################################################################
    # TELEGRAM BEFEHL: /info - Zeige Infos
    ################################################################################
    async def tg_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Zeige Hilfenachricht mit allen verfügbaren Befehlen"""
        info_msg = """ℹ️ Vinted Scraper Bot - Informationen

🤖 Dieser Bot wurde von python_tutorials_de erstellt.
Er durchsucht Vinted nach neuen Artikeln und sendet dir automatisch Benachrichtigungen!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Telegram Commands:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 /id → Zeige deine Chat ID an
🔄 /start [Begriff] → Starte kontinuierliche Suche
🔍 /suche [Begriff] → Einmalige Schnellsuche
⏹️ /stop → Stoppe den laufenden Scraper
ℹ️ /info → Diese Nachricht

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Features:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Echtzeitbenachrichtigungen für neue Artikel
📸 Produktfoto automatisch mitgesendet
💰 Preisanzeige in EUR
🔗 Direkter Link zum Artikel auf Vinted

💡 Beispiele:
/start Nike Turnschuhe - Sucht nach Nike Turnschuhen
/suche Adidas - Nur eine einmalige Suche
/stop - Beendet die aktuelle Suche"""
        await update.message.reply_text(info_msg)

    ################################################################################
    # TELEGRAM BEFEHL: /suche [Begriff] - Schnellsuche
    ################################################################################
    async def tg_suche(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Mach eine schnelle einmalige Suche"""
        global prozess
        if not context.args:
            await update.message.reply_text("❌ Bitte Suchbegriff angeben!\n\n📝 Beispiel: /suche nike")
            return
        
        neuer_begriff = " ".join(context.args)
        # set_suchbegriff(neuer_begriff)  # Diese Funktion existiert nicht, daher auskommentiert
        if prozess:
            prozess.kill()
        await update.message.reply_text(f"🔍 Einmalige Schnellsuche für: '{neuer_begriff}'...")
        log_suche(neuer_begriff)
        
        try:
            # Erstelle neue Session
            session = requests.Session()
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "de-DE,de;q=0.9",
                "Referer": "https://www.vinted.de/",
            })
            session.get("https://www.vinted.de", timeout=10)
            
            # Suche auf Vinted API
            url = "https://www.vinted.de/api/v2/catalog/items"
            params = {"search_text": neuer_begriff, "order": "newest_first", "per_page": 10, "page": 1, "country_ids": ",".join(str(i) for i in range(1, 33))}
            response = session.get(url, params=params, timeout=10)
            response.raise_for_status()
            artikel = response.json().get("items", [])

            if artikel:
                await update.message.reply_text(f"✨ {len(artikel)} aktuelle Artikel gefunden!")
                for a in artikel:
                    foto = ""
                    if a.get("photo") and a["photo"].get("url"):
                        foto = a["photo"]["url"]
                    link = f"https://www.vinted.de/items/{a['id']}"
                    preis = a.get('price', {})
                    preis_text = f"{preis.get('amount', 'N/A')} {preis.get('currency_code', 'EUR')}" if isinstance(preis, dict) else f"{preis} EUR"
                    nachricht = f"📦 {a['title']}\n💶 {preis_text}\n🔗 {link}"
                    if foto:
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
                                      data={"chat_id": Chat_ID, "caption": nachricht, "photo": foto})
                    else:
                        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                                      data={"chat_id": Chat_ID, "text": nachricht})
                await update.message.reply_text("✅ Schnellsuche abgeschlossen!")
            else:
                await update.message.reply_text(f"🔍 Keine Artikel gefunden für: '{neuer_begriff}'")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Fehler:\n❌ {str(e)}")

    ################################################################################
    # TELEGRAM COMMAND HANDLER - Registriere alle Befehle
    ################################################################################
    # Sag dem Bot welche Funktionen zu welchen Befehlen gehören
    app.add_handler(CommandHandler("id", tg_id))
    app.add_handler(CommandHandler("start", tg_start))
    app.add_handler(CommandHandler("stop", tg_stop))
    app.add_handler(CommandHandler("info", tg_info))
    app.add_handler(CommandHandler("suche", tg_suche))

    ################################################################################
    # STARTE BEIDE BOTS GLEICHZEITIG
    ################################################################################
    # Diese Funktion startet Discord und Telegram parallel
    
    async def main():
        keep_alive()  # Starte den Keep-Alive Webserver (für Render.com)
        """Einstiegspunkt - Hier werden beide Bots gestartet"""
        async with bot:
            # Starte Discord Bot
            asyncio.create_task(bot.start(TOKENDISCORD))
            
            # Initialisiere Telegram App
            await app.initialize()
            await app.start()
            
            # Sende Start-Nachricht zu Telegram
            await app.bot.send_message(chat_id=Chat_ID, text=startup_msg)
            print(startup_msg)
            
            # Starte Telegram Polling (höre auf neue Nachrichten)
            await app.updater.start_polling()
            
            # Warte ewig (bis Ctrl+C gedrückt wird)
            await asyncio.Event().wait()

    # Starte die main() Funktion
    asyncio.run(main())

################################################################################
# FEHLERBEHANDLUNG
################################################################################
except Exception as e:
    print("Programm beendet ✅", e)  # Falls etwas schief geht, zeige den Fehler