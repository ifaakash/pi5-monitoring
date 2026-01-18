import subprocess
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

def get_listening_ports():
    cmd = "ss -tulnpH | grep LISTEN"
    result = subprocess.run(
        cmd,
        shell=True,
        text=True,
        capture_output=True
    )

    listeners = []

    for line in result.stdout.splitlines():
        parts = line.split()
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
            "interface": iface,
            "family": family,
            "scope": classify_scope(ip)
        })

    return listeners


def classify_scope(ip):
    if ip.startswith("127.") or ip == "::1":
        return "loopback"
    if ip == "0.0.0.0" or ip == "::":
        return "all_interfaces"
    if ip.startswith("192.168.") or ip.startswith("10.") or ip.startswith("100."):
        return "lan"
    return "public"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/ports":
            data = get_listening_ports()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data, indent=2).encode())
        else:
            self.send_response(404)
            self.end_headers()


HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
