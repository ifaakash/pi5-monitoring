import subprocess
import re
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

def get_listening_ports():
    listeners = []

    if platform.system() == "Darwin":
        cmd = "lsof -i -P -n | grep LISTEN"
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) < 9: continue
            
            address = parts[-2]
            proto = parts[-3].lower()
            family = parts[4].lower()
            
            if ":" in address:
                ip_port = address.rsplit(":", 1)
                ip = ip_port[0]
                port = ip_port[1]
                if ip == "*": ip = "0.0.0.0" if family == "ipv4" else "::"
            else:
                continue

            listeners.append({
                "protocol": proto,
                "ip": ip,
                "port": int(port),
                "family": family,
                "scope": classify_scope(ip)
            })
    else:
        cmd = "ss -tulnpH | grep LISTEN"
        result = subprocess.run(
            cmd,
            shell=True,
            text=True,
            capture_output=True
        )
    
        for line in result.stdout.splitlines():
            parts = line.split()
            if len(parts) < 5: continue
            proto = parts[0]
            local = parts[4]
    
            # Handle IPv6 [::]:22
            if local.startswith("["):
                addr_port = local.split("]:")
                ip = addr_port[0].strip("[")
                port = addr_port[1]
                family = "ipv6"
                iface = None
            else:
                # IPv4 127.0.0.53%lo:53
                ip_port = local.rsplit(":", 1)
                ip_iface = ip_port[0]
                port = ip_port[1]
    
                if "%" in ip_iface:
                    ip, iface = ip_iface.split("%", 1)
                else:
                    ip = ip_iface
                    iface = None
    
                family = "ipv4"
    
            listeners.append({
                "protocol": proto,
                "ip": ip,
                "port": int(port),
                # "interface": iface,
                "family": family,
                "scope": classify_scope(ip)
            })

    listeners.sort(key=lambda x: x["port"])
    return listeners

def get_uptime():
    with open("/proc/uptime", "r") as f:
        seconds = float(f.read().split()[0])

    minutes = int(seconds // 60)
    hours = minutes // 60
    days = hours // 24

    return {
        "seconds": int(seconds),
        "minutes": minutes,
        "human": f"{days}d {hours % 24}h {minutes % 60}m"
    }

import platform

def check_network():
    # Detect OS for correct ping timeout syntax
    # Linux: -W 2 (2 seconds)
    # macOS: -W 2000 (2000 milliseconds)
    param = "-W"
    if platform.system().lower() == "darwin":
        timeout = "2000" 
    else:
        timeout = "2"

    result = subprocess.run(
        ["ping", "-c", "2", param, timeout, "8.8.8.8"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0

def check_dns():
    try:
        # Set a specific timeout for this socket operation
        socket.setdefaulttimeout(2) 
        socket.gethostbyname("google.com")
        return True
    except (socket.gaierror, socket.timeout):
        return False

def network_status():
    network_ok = check_network()
    dns_ok = check_dns()

    if network_ok and dns_ok:
        status = "online"
    elif network_ok and not dns_ok:
        status = "network_ok_dns_broken"
    else:
        status = "offline"

    return {
        "network": network_ok,
        "dns": dns_ok,
        "status": status
    }


def get_health():
    return {
        "uptime": get_uptime(),
        "connectivity": network_status()
    }


def classify_scope(ip):
    if ip.startswith("127.") or ip == "::1":
        return "loopback"
    if ip == "0.0.0.0" or ip == "::":
        return "all_interfaces"
    if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("100."):
        return "lan"
    return "public"


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, data):
        """Helper to send JSON response"""
        try:
            response = json.dumps(data, indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response)))
            self.end_headers()
            self.wfile.write(response)
        except Exception as e:
            print(f"Error sending response: {e}")

    def do_GET(self):
        if self.path == "/ports":
            data = get_listening_ports()
            self._send_json(data)
        elif self.path == "/health":
            data = get_health()
            self._send_json(data) # <--- FIXED: Now actually sends data
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    print("Server listening on 0.0.0.0:8080...")
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
