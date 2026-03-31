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
sys.stdout.reconfigure(line_buffering=True)  # Damit Text sofort gezeigt wird (nicht gepuffert)

try:
    ################################################################################
    # IMPORTS - Alles was wir brauchen
    ################################################################################
    # pyfiglet: Erstellt großen Text-Banner (für cooleres Aussehen)
    from pyfiglet import figlet_format
    
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

    from telegram import Update
    from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
    import discord
    from discord.ext import commands
    from dotenv import load_dotenv
    import asyncio
    import os
    import subprocess
    import json
    from config import TOKEN, Chat_ID
    from data_telegram import log_suche
    import requests

    ################################################################################
    # GLOBALE PROZESS-VARIABLEN
    ################################################################################
    logprozess = None          # Für das Dashboard (optional)
    prozess = None             # Der Telegram Scraper Prozess
    discord_prozess = None     # Der Discord Scraper Prozess
    SEEN_FILE = "seen.json"    # Datei mit Artikel die wir schon gesehen haben

    ################################################################################
    # OPTIONAL: Dashboard starten
    ################################################################################
    # Wenn du ein schönes Dashboard möchtest, uncomment diese Zeile:
    # logprozess = subprocess.Popen(["python", "log_viewer.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
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
    
    if not TOKENDISCORD:
        print("❌ FEHLER: DISCORD_TOKEN nicht geladen!")
        print("   Prüfe: .env Datei existiert im selben Verzeichnis wie main.py")
        print("   Prüfe: DISCORD_TOKEN=... ist in .env definiert")
        sys.exit(1)  # Beende mit Fehler
    
    if not TOKEN:
        print("❌ FEHLER: TELEGRAM_TOKEN nicht geladen!")
        print("   Prüfe: .env Datei existiert")
        print("   Prüfe: TELEGRAM_TOKEN=... ist in .env definiert")
        sys.exit(1)  # Beende mit Fehler

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
                    startup_msg = (
                        "🚀 **Vinted Scraper Bot online!**\n\n"
                        "Der Bot wurde erfolgreich gestartet und ist einsatzbereit.\n"
                        "Nutze `!start <suchbegriff>`, um eine neue Suche zu starten!\n"
                        "Nutze `!stop`, um die aktuelle Suche zu beenden.\n"
                        "Nutze `!info`, um weitere Informationen über den Bot zu erhalten.\n"
                    )
                    await channel.send(startup_msg)
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

    ################################################################################
    # DISCORD BEFEHL: !start [Begriff] - Starte kontinuierlichen Scraper
    ################################################################################
    @bot.command(name="start")
    async def discord_start(ctx, *, begriff=None):
        """
        Starte einen neuen Vinted-Scraper mit einem Suchbegriff
        Beispiel: !start Nike Turnschuhe
        """
        global discord_prozess  # Verwende die globale Variable
        
        # Fehlerbehandlung: Suchbegriff vorhanden?
        if not begriff:
            await ctx.send("❌ Bitte Suchbegriff angeben!\n\n📝 Beispiel: `!start nike`")
            return

        # Falls bereits ein Scraper läuft, stoppe ihn
        if discord_prozess:
            discord_prozess.kill()
            print("Alter Scraper gestoppt ✅")

        # Nachrichten senden
        await ctx.send(f"🚀 Vinted Scraper gestartet!")
        await ctx.send(f"🔍 Suchbegriff: `{begriff}`\n⏱️ Läuft kontinuierlich...\n📲 Du erhältst Benachrichtigungen hier im Channel!")
        print(f"🚀 Discord Scraper gestartet: {begriff}")
        
        # Starte data_discord.py als separaten Prozess im Hintergrund
        # Übergebe: Channel-ID und Suchbegriff als Argumente
        discord_prozess = subprocess.Popen(["python", "data_discord.py", str(ctx.channel.id), begriff])

    ################################################################################
    # DISCORD BEFEHL: !stop - Stoppe den Scraper
    ################################################################################
    @bot.command(name="stop")
    async def discord_stop(ctx):
        """Stoppe den laufenden Scraper"""
        global discord_prozess
        
        if discord_prozess:
            discord_prozess.kill()  # Beende den Prozess
            discord_prozess = None
            await ctx.send("⏹️ Vinted Scraper gestoppt!\n💤 Keine neuen Benachrichtigungen mehr.")
            print("⏹️ Discord Scraper gestoppt")
        else:
            await ctx.send("⚠️ Kein aktiver Scraper läuft!")

    ################################################################################
    # DISCORD BEFEHL: !info - Zeige Informationen
    ################################################################################
    @bot.command(name="info")
    async def discord_info(ctx):
        """Zeige eine Hilfenachricht mit allen Befehlen"""
        info_msg = """ℹ️ **Bot-Informationen**

Dieser Bot wurde von **python_tutorials_de** erstellt.
Er durchsucht Vinted nach neuen Artikeln und sendet Benachrichtigungen!

📋 **Verfügbare Befehle:**
💡 `!id` → Deine Discord ID
🔄 `!start [Begriff]` → Kontinuierliche Überwachung
🔍 `!suche [Begriff]` → Einmalige Schnellsuche
⏹️ `!stop` → Laufende Suche stoppen
ℹ️ `!info` → Diese Nachricht

✨ **Features:**
✅ Echtzeit-Benachrichtigungen
📸 Mit Produktfotos
💰 Preisanzeige
🔗 Direkte Vinted-Links"""
        await ctx.send(info_msg)

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
    
    startup_msg = """🤖 **Telegram-Vinted-Bot gestartet!** 🚀

📋 **Verfügbare Befehle:**
💡 /id → Zeige deine Chat ID an
🔄 /start [Begriff] → Kontinuierliche Vinted-Suche
🔍 /suche [Begriff] → Einmalige Schnellsuche
⏹️ /stop → Scraper stoppen
ℹ️ /info → Bot-Informationen"""

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
        await update.message.reply_text("🚀 Vinted Scraper gestartet!")
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
        """Zeige Hilfenachricht"""
        info_msg = """ℹ️ **Bot-Informationen**

Dieser Bot wurde von python_tutorials_de erstellt.

📋 **Verfügbare Befehle:**
💡 /id → Deine Chat ID
🔄 /start [Begriff] → Kontinuierliche Überwachung
🔍 /suche [Begriff] → Einmalige Schnellsuche
⏹️ /stop → Laufende Suche stoppen
ℹ️ /info → Diese Nachricht

✨ **Features:**
✅ Echtzeit-Benachrichtigungen
📸 Mit Produktfotos
💰 Preisanzeige
🔗 Direkte Vinted-Links"""
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
            params = {"search_text": neuer_begriff, "order": "newest_first", "per_page": 10, "page": 1}
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