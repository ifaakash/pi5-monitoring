from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import monitoring

# --- HTML TEMPLATE ---

def render_html(health, ports):
    # Status Logic
    is_online = health['status'] == "Online"
    status_text = health['status']
    
    # Theme Colors
    bg_color = "#1a1b26" # Tokyo Night / Dark Slate
    card_bg = "#24283b"
    text_color = "#c0caf5"
    primary = "#7aa2f7"
    success = "#9ece6a"
    error = "#f7768e" 
    warning = "#e0af68"
    
    if is_online:
        status_color = success
    elif status_text == "DNS Error":
        status_color = warning
    else:
        status_color = error

    # Generate Ports Rows
    port_rows = ""
    for p in ports:
        badge_color = "#bb9af7" if p['protocol'] == "udp" else "#7dcfff"
        port_rows += f"""
        <div class="row">
            <div class="col"><span class="badge" style="background: {badge_color}15; color: {badge_color}; border: 1px solid {badge_color}40;">{p['protocol'].upper()}</span></div>
            <div class="col" style="font-weight: bold; color: {text_color};">{p['port']}</div>
            <div class="col mono">{p['ip']}</div>
            <div class="col" style="opacity: 0.7;">{p['scope']}</div>
        </div>"""
    
    # Generate Process Rows
    proc_rows = ""
    for p in health['processes']:
        proc_rows += f"""
        <div class="row">
            <div class="col mono" style="opacity: 0.7;">{p['pid']}</div>
            <div class="col" style="font-weight: 500;">{p['name']}</div>
            <div class="col" style="color: {primary}; text-align: right;">{p['memory_mb']} MB</div>
        </div>"""

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>System Monitor</title>
        <meta http-equiv="refresh" content="60">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: {bg_color};
                --card: {card_bg};
                --text: {text_color};
                --primary: {primary};
                --success: {success};
                --error: {error};
            }}
            * {{ box-sizing: border-box; }}
            body {{
                font-family: 'Inter', sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 40px 20px;
                line-height: 1.5;
            }}
            .container {{ max_width: 1000px; margin: 0 auto; }}
            
            /* Header */
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 40px;
                padding-bottom: 20px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }}
            h1 {{ margin: 0; font-size: 24px; font-weight: 700; color: white; letter-spacing: -0.5px; }}
            .uptime {{ font-size: 14px; opacity: 0.7; font-family: 'JetBrains Mono', monospace; }}
            
            /* Grid */
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }}
            
            /* Card */
            .card {{
                background: var(--card);
                border-radius: 12px;
                padding: 24px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.2);
                border: 1px solid rgba(255,255,255,0.05);
            }}
            .card h2 {{
                margin: 0 0 20px 0;
                font-size: 16px;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-weight: 600;
                color: rgba(255,255,255,0.4);
            }}
            
            /* Status */
            .status-box {{
                display: flex;
                align-items: center;
                gap: 15px;
                background: rgba(0,0,0,0.2);
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
            }}
            .indicator {{ width: 12px; height: 12px; border-radius: 50%; background: {status_color}; box-shadow: 0 0 10px {status_color}80; }}
            .status-text {{ font-size: 18px; font-weight: 700; color: white; }}
            
            .checks {{ display: flex; gap: 10px; font-size: 14px; }}
            .check-item {{ background: rgba(255,255,255,0.05); padding: 5px 10px; border-radius: 4px; }}
            
            /* List / Table Styles */
            .row {{
                display: flex;
                align-items: center;
                padding: 12px 0;
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }}
            .row:last-child {{ border-bottom: none; }}
            .col {{ flex: 1; }}
            .mono {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; }}
            
            /* Badge */
            .badge {{
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 700;
                font-family: 'JetBrains Mono', monospace;
            }}
            
            a {{ color: var(--text); opacity: 0.5; text-decoration: none; font-size: 12px; display: block; margin-top: 30px; text-align: center; }}
            a:hover {{ opacity: 1; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Server Dashboard</h1>
                <div class="uptime">UP: {health['uptime']}</div>
            </div>

            <div class="grid">
                <!-- Health Card -->
                <div class="card">
                    <h2>System Status</h2>
                    <div class="status-box">
                        <div class="indicator"></div>
                        <div class="status-text">{health['status']}</div>
                    </div>
                    <div class="checks">
                        <div class="check-item">Network: {"✅" if health['network'] else "❌"}</div>
                        <div class="check-item">DNS: {"✅" if health['dns'] else "❌"}</div>
                    </div>
                </div>

                <!-- Memory Card -->
                <div class="card">
                    <h2>Top Memory Processes</h2>
                    <div class="processes">
                        {proc_rows}
                    </div>
                </div>
                
                <!-- Ports Card (Full Width) -->
                <div class="card" style="grid-column: 1 / -1;">
                    <h2>Open Ports</h2>
                    <div class="ports-list">
                        <div class="row" style="opacity: 0.5; font-size: 12px; text-transform: uppercase; font-weight: 600;">
                            <div class="col">Protocol</div>
                            <div class="col">Port</div>
                            <div class="col">Listen Address</div>
                            <div class="col">Scope</div>
                        </div>
                        {port_rows}
                    </div>
                </div>
            </div>
            
            <a href="/json">VIEW JSON API</a>
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
            data = monitoring.get_listening_ports()
            self._send_response(json.dumps(data, indent=2))

        elif self.path == "/health":
            data = monitoring.get_health()
            self._send_response(json.dumps(data, indent=2))

        elif self.path == "/":
            # Gather all data for the HTML view
            health_data = monitoring.get_health()
            ports_data = monitoring.get_listening_ports()
            html_content = render_html(health_data, ports_data)
            self._send_response(html_content, "text/html")

        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    print("Server running at http://0.0.0.0:8080/")
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
