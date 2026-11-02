#!/usr/bin/env python3
"""
Servidor HTTP local para el proyecto Imperio Español 1794.
Cesium no funciona con file:// debido a restricciones CORS.

Uso:
    python3 server.py
    
Después abre: http://localhost:8000
"""
import http.server
import socketserver
import sys
import webbrowser
import os

PORT = 8000

class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        '.geojson': 'application/json',
        '.glb': 'model/gltf-binary',
        '.gltf': 'model/gltf+json',
    }

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

    def log_message(self, format, *args):
        # Quieter logs
        if '404' in str(args) or '500' in str(args):
            super().log_message(format, *args)


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            url = f"http://localhost:{PORT}"
            print(f"\n  🌎  Servidor activo en {url}")
            print(f"     Ctrl+C para detener.\n")
            try:
                webbrowser.open(url)
            except Exception:
                pass
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Servidor detenido.\n")
        sys.exit(0)
    except OSError as e:
        if e.errno in (48, 98, 10048):   # macOS, Linux, Windows
            print(f"\n  ⚠️  El puerto {PORT} está ocupado. Cierra el otro proceso o cambia PORT en server.py.\n")
        else:
            raise


if __name__ == "__main__":
    main()
