"""
Simple HTTP server to serve test websites for Selenium testing.

Usage:
    python serve_test_sites.py

This will start a server at:
    - http://localhost:8000/login  -> Login page
    - http://localhost:8000/signup -> Signup page
"""

import http.server
import socketserver
import os

PORT = 8000
DIRECTORY = "test_websites"


class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def do_GET(self):
        # Serve index.html for directory paths
        if self.path == "/login" or self.path == "/login/":
            self.path = "/login/index.html"
        elif self.path == "/signup" or self.path == "/signup/":
            self.path = "/signup/index.html"
        elif self.path == "/" or self.path == "":
            self.path = "/login/index.html"
        
        return super().do_GET()


def main():
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        print(f"\n{'='*50}")
        print(f"  🚀 Test Server Running!")
        print(f"{'='*50}")
        print(f"\n  📍 Login page:  http://localhost:{PORT}/login")
        print(f"  📍 Signup page: http://localhost:{PORT}/signup")
        print(f"\n  📋 Valid credentials: admin / password123")
        print(f"\n  Press Ctrl+C to stop")
        print(f"{'='*50}\n")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n  👋 Server stopped.\n")


if __name__ == "__main__":
    main()
