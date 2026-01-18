import subprocess
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time

# --- DATA GATHERING FUNCTIONS ---

def get_listening_ports():
    cmd = "ss -tulnpH | grep LISTEN"
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    listeners = []

    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5: continue # Safety check
        
        proto = parts[0]
        local = parts[4]
        
        # Handle IPv6 [::]:22 vs IPv4 0.0.0.0:80
        if local.startswith("["):
            addr_port = local.split("]:")
            ip = addr_port[0].strip("[")
            port = addr_port[1]
            family = "ipv6"
        else:
            ip_port = local.rsplit(":", 1)
            ip_iface = ip_port[0]
            port = ip_port[1]
            if "%" in ip_iface:
                ip = ip_iface.split("%", 1)[0]
            else:
                ip = ip_iface
            family = "ipv4"

        listeners.append({
            "protocol": proto,
            "ip": ip,
            "port": int(port),
            "family": family,
            "scope": classify_scope(ip)
        })
    return listeners

def classify_scope(ip):
    if ip.startswith("127.") or ip == "::1": return "Localhost"
    if ip == "0.0.0.0" or ip == "::": return "All Interfaces"
    if ip.startswith("192.168.") or ip.startswith("10."): return "LAN"
    return "Public"

def get_uptime():
    try:
        with open("/proc/uptime", "r") as f:
            seconds = float(f.read().split()[0])
        minutes = int(seconds // 60)
        hours = minutes // 60
        days = hours // 24
        return f"{int(days)}d {int(hours % 24)}h {int(minutes % 60)}m"
    except:
        return "Unknown"

def check_network():
    # Reduced count and wait time for speed
    res = subprocess.run(["ping", "-c", "1", "-W", "1", "8.8.8.8"], stdout=subprocess.DEVNULL)
    return res.returncode == 0

def check_dns():
    try:
        socket.setdefaulttimeout(1)
        socket.gethostbyname("google.com")
        return True
    except:
        return False

def get_health():
    net = check_network()
    dns = check_dns()
    
    if net and dns: status = "Online"
    elif net and not dns: status = "DNS Error"
    else: status = "Offline"

    return {
        "uptime": get_uptime(),
        "network": net,
        "dns": dns,
        "status": status
    }

# --- HTML TEMPLATE ---

def render_html(health, ports):
    # Determine status color
    status_color = "#2ecc71" if health['status'] == "Online" else "#e74c3c"
    if health['status'] == "DNS Error": status_color = "#f39c12"

    # Generate Table Rows
    rows = ""
    for p in ports:
        rows += f"""
        <tr>
            <td><span class="badge {p['protocol']}">{p['protocol']}</span></td>
            <td>{p['port']}</td>
            <td class="mono">{p['ip']}</td>
            <td>{p['scope']}</td>
        </tr>"""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Server Status</title>
        <meta http-equiv="refresh" content="60"> <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f4f6f8; margin: 0; padding: 40px; color: #333; }}
            .container {{ max_width: 800px; margin: 0 auto; }}
            
            /* Cards */
            .card {{ background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); padding: 25px; margin-bottom: 20px; }}
            
            /* Header Section */
            .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
            .status-dot {{ height: 12px; width: 12px; background-color: {status_color}; border-radius: 50%; display: inline-block; margin-right: 8px; }}
            .uptime {{ color: #666; font-size: 0.9em; }}
            
            /* Table Styling */
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th {{ text-align: left; color: #888; font-weight: 600; font-size: 0.85em; text-transform: uppercase; padding-bottom: 15px; border-bottom: 2px solid #eee; }}
            td {{ padding: 12px 0; border-bottom: 1px solid #f0f0f0; }}
            tr:last-child td {{ border-bottom: none; }}
            
            /* Utility */
            .mono {{ font-family: 'Monaco', 'Consolas', monospace; color: #555; }}
            .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold; color: white; }}
            .tcp {{ background: #3498db; }}
            .udp {{ background: #9b59b6; }}
            
            h2 {{ margin-top: 0; font-size: 1.2em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Server Dashboard</h1>
                <div class="uptime">Up: {health['uptime']}</div>
            </div>

            <div class="card">
                <h2>System Health</h2>
                <div style="font-size: 1.5em; font-weight: bold; display: flex; align-items: center;">
                    <span class="status-dot"></span> {health['status']}
                </div>
                <div style="margin-top: 10px; color: #666;">
                    Network: {"✅" if health['network'] else "❌"} &nbsp;|&nbsp; 
                    DNS: {"✅" if health['dns'] else "❌"}
                </div>
            </div>

            <div class="card">
                <h2>Open Ports</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Protocol</th>
                            <th>Port</th>
                            <th>Listen Address</th>
                            <th>Access Scope</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>
            <div style="text-align: center; color: #aaa; font-size: 0.8em; margin-top: 20px;">
                <a href="/json" style="color: #aaa; text-decoration: none;">View JSON Data</a>
            </div>
        </div>
    </body>
    </html>
    """
    return html

# --- SERVER HANDLER ---

class Handler(BaseHTTPRequestHandler):
    def _send_response(self, content, content_type="application/json"):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(content.encode())

    def do_GET(self):
        if self.path == "/ports":
            data = get_listening_ports()
            self._send_response(json.dumps(data, indent=2))
            
        elif self.path == "/health":
            data = get_health()
            self._send_response(json.dumps(data, indent=2))
            
        elif self.path == "/":
            # Gather all data for the HTML view
            health_data = get_health()
            ports_data = get_listening_ports()
            html_content = render_html(health_data, ports_data)
            self._send_response(html_content, "text/html")
            
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    print("Server running at http://0.0.0.0:8080/")
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
