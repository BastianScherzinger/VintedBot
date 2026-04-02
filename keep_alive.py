from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b"Vinted Bot ist online und wach!")
    
    # Unterdrückt die Logs bei jedem Ping, damit deine Konsole sauber bleibt
    def log_message(self, format, *args):
        pass

def run_server():
    # Render weist den Port über die Umgebungsvariable PORT zu
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    print(f"🌐 Webserver gestartet auf Port {port} (Keep-Alive für Render)")
    server.serve_forever()

def keep_alive():
    """Startet den Webserver in einem Hintergrund-Thread"""
    t = Thread(target=run_server)
    t.daemon = True  # Thread beendet sich automatisch, wenn der Bot gestoppt wird
    t.start()