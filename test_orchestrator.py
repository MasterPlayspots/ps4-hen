#!/usr/bin/env python3
import http.server
import socketserver
import subprocess
import threading
import time
import sys
import os

HTTP_PORT = 8080
SERIAL_DEVICE = "/dev/tty.usbserial-XXXX"   # Replace if you have a serial adapter
PAYLOAD_FILE = "installer/hen.bin"

class Orchestrator:
    def __init__(self):
        self.log = []
        self.serial_thread = None
        self.http_thread = None
        self.test_passed = False

    def start_http_server(self):
        handler = http.server.SimpleHTTPRequestHandler
        self.httpd = socketserver.TCPServer(("", HTTP_PORT), handler)
        self.httpd.serve_forever()

    def monitor_serial(self):
        try:
            proc = subprocess.Popen(
                ["screen", "-L", "-Logfile", "serial.log", SERIAL_DEVICE, "115200"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            for line in iter(proc.stdout.readline, b''):
                line_str = line.decode(errors='ignore')
                self.log.append(("SERIAL", line_str))
                if "HEN enabled" in line_str or "payload loaded" in line_str:
                    self.test_passed = True
                    self.log.append(("INFO", "HEN success detected in serial log"))
        except Exception as e:
            self.log.append(("ERROR", f"Serial monitor failed: {e}"))

    def check_network_services(self):
        time.sleep(5)
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            # Replace with your PS4's IP address
            result = s.connect_ex(('192.168.1.XXX', 2121))
            if result == 0:
                self.log.append(("NETWORK", "FTP service detected – HEN likely active"))
                self.test_passed = True
            else:
                self.log.append(("NETWORK", "FTP service not reachable"))
        except Exception as e:
            self.log.append(("ERROR", f"Network check failed: {e}"))

    def run(self):
        self.http_thread = threading.Thread(target=self.start_http_server, daemon=True)
        self.http_thread.start()
        print(f"HTTP server running on port {HTTP_PORT}. Point PS4 browser to http://<your-mac-ip>:{HTTP_PORT}/exploit.html")

        if os.path.exists(SERIAL_DEVICE):
            self.serial_thread = threading.Thread(target=self.monitor_serial, daemon=True)
            self.serial_thread.start()
        else:
            self.log.append(("WARNING", f"Serial device {SERIAL_DEVICE} not found. Skipping serial monitor."))

        input("Press ENTER after you have loaded the exploit page on the PS4...")

        self.check_network_services()

        print("\n=== Test Log ===")
        for entry in self.log:
            print(f"[{entry[0]}] {entry[1]}")
        print(f"\nTest passed: {self.test_passed}")

if __name__ == "__main__":
    orch = Orchestrator()
    orch.run()
