from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import monitoring

# --- HTML TEMPLATE ---

def render_html(health, ports):
    # Grafana-inspired variables
    # Dark Theme
    bg_color = "#101217"       # Very dark, almost black
    panel_bg = "#181b1f"       # Slightly lighter for cards
    header_on_panel = "#22252b" # Header background for panels
    text_main = "#dce4e9"      # Off-white
    text_muted = "#9fa7b3"     # Muted text
    border_color = "#2c3235"   # Subtle borders
    
    # Grafana Brand Colors
    orange = "#FF9900"
    blue = "#5794F2"
    green = "#73BF69"
    red = "#F2495C"
    purple = "#B877D9"
    
    # Logic
    is_online = health['status'] == "Online"
    if is_online:
        status_color = green
        status_icon = "check" # Using simple CSS shapes/text instead of complex SVGs for simplicity unless inline
    elif health['status'] == "DNS Error":
        status_color = orange
    else:
        status_color = red

    # Process Rows
    proc_rows = ""
    for p in health['processes']:
        proc_rows += f"""
        <div class="table-row">
            <div class="col mono" style="color: {orange};">{p['pid']}</div>
            <div class="col" style="font-weight: 500; color: {text_main};">{p['name']}</div>
            <div class="col right" style="color: {blue};">{p['memory_mb']} MB</div>
            <div class="col right graph-col">
                <div class="bar-bg"><div class="bar-fill" style="width: {min(p['memory_mb']/10, 100)}%; background-color: {blue};"></div></div>
            </div>
        </div>"""

    # Port Rows
    port_rows = ""
    for p in ports:
        badge_style = f"background: rgba(50, 116, 217, 0.15); color: {blue}; border: 1px solid rgba(50, 116, 217, 0.3);"
        if p['protocol'] == 'udp':
            badge_style = f"background: rgba(184, 119, 217, 0.15); color: {purple}; border: 1px solid rgba(184, 119, 217, 0.3);"
            
        scope_color = green if p['scope'] == 'Public' else text_muted
        
        port_rows += f"""
        <div class="table-row">
            <div class="col"><span class="badge" style="{badge_style}">{p['protocol'].upper()}</span></div>
            <div class="col mono" style="color: {orange};">{p['port']}</div>
            <div class="col mono" style="color: {text_main};">{p['ip']}</div>
            <div class="col" style="color: {scope_color};">{p['scope']}</div>
        </div>"""

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Pi5 Dashboard</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Roboto+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: {bg_color};
                --panel: {panel_bg};
                --header: {header_on_panel};
                --text: {text_main};
                --muted: {text_muted};
                --border: {border_color};
                --blue: {blue};
                --green: {green};
                --orange: {orange};
                --red: {red};
            }}
            * {{ box-sizing: border-box; }}
            body {{
                font-family: 'Inter', sans-serif;
                background-color: var(--bg);
                color: var(--text);
                margin: 0;
                padding: 20px;
                font-size: 14px;
            }}
            .navbar {{
                display: flex;
                align-items: center;
                gap: 15px;
                margin-bottom: 25px;
                padding-bottom: 20px;
                border-bottom: 1px solid var(--border);
            }}
            .logo-icon {{
                width: 32px; height: 32px;
                background: linear-gradient(135deg, var(--orange), #FF4400);
                mask: url('data:image/svg+xml;utf8,<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 7l10 5 10-5-10-5zm0 9l2.5-1.25L12 8.5l-2.5 1.25L12 11zm0 2.5l-5-2.5-5 2.5L12 22l10-8.5-5-2.5-5 2.5z"/></svg>'); 
                -webkit-mask: url('data:image/svg+xml;utf8,<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M12 2L2 7l10 5 10-5-10-5zm0 9l2.5-1.25L12 8.5l-2.5 1.25L12 11zm0 2.5l-5-2.5-5 2.5L12 22l10-8.5-5-2.5-5 2.5z"/></svg>') no-repeat center;
                -webkit-mask-size: contain;
                border-radius: 4px; /* Fallback shape */
            }}
            h1 {{ font-weight: 500; font-size: 20px; margin: 0; }}
            
            .dashboard-grid {{
                display: grid;
                grid-template-columns: repeat(12, 1fr);
                gap: 16px;
            }}
            
            .panel {{
                background: var(--panel);
                border: 1px solid var(--border);
                border-radius: 2px;
                display: flex;
                flex-direction: column;
            }}
            
            .panel-header {{
                background: var(--header);
                padding: 8px 12px;
                font-size: 13px;
                font-weight: 600;
                color: var(--muted);
                border-bottom: 1px solid var(--border);
                display: flex;
                align-items: center;
                justify-content: space-between;
                cursor: pointer;
            }}
            .panel-header:hover {{ color: var(--text); }}
            
            .panel-content {{ padding: 16px; flex: 1; }}
            
            /* Stat Panel */
            .stat-value {{ font-size: 32px; font-weight: 500; line-height: 1.2; }}
            .stat-label {{ color: var(--muted); font-size: 12px; }}
            
            /* Status Indicator */
            .status-indicator {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 12px;
                font-weight: 600;
                font-size: 12px;
                background: rgba(0,0,0,0.2);
                border: 1px solid transparent;
            }}
            
            /* Tables/Lists */
            .table-row {{
                display: flex;
                align-items: center;
                padding: 8px 0;
                border-bottom: 1px solid rgba(255,255,255,0.03);
            }}
            .table-row:last-child {{ border-bottom: none; }}
            .table-header {{
                font-size: 12px; color: var(--blue); font-weight: 600;
                padding-bottom: 8px; border-bottom: 2px solid var(--border);
            }}
            .col {{ flex: 1; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; padding-right: 10px; }}
            .col.right {{ text-align: right; }}
            .mono {{ font-family: 'Roboto Mono', monospace; font-size: 12px; }}
            
            .badge {{
                font-size: 10px; padding: 2px 6px; border-radius: 3px; font-weight: 600; font-family: 'Roboto Mono';
            }}
            
            /* Mini Bar Graph */
            .graph-col {{ max-width: 60px; }}
            .bar-bg {{ height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; overflow: hidden; margin-top: 6px; }}
            .bar-fill {{ height: 100%; border-radius: 2px; }}

            /* Scrollable List */
            .scroll-list {{
                max-height: 300px;
                overflow-y: auto;
                overflow-x: hidden;
            }}
            /* Custom Scrollbar */
            .scroll-list::-webkit-scrollbar {{ width: 6px; }}
            .scroll-list::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.02); }}
            .scroll-list::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 3px; }}
            .scroll-list::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.2); }}

            /* Refresh Select */
            .refresh-select {{
                background: #181b1f;
                color: var(--text);
                border: 1px solid var(--border);
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                margin-left: 10px;
                cursor: pointer;
            }}
            .refresh-select:focus {{ outline: none; border-color: var(--blue); }}

            /* Grid Layout Positions */
            .panel-status {{ grid-column: span 4; }}
            .panel-uptime {{ grid-column: span 4; }}
            .panel-health {{ grid-column: span 4; }}
            .panel-memory {{ grid-column: span 6; }}
            .panel-ports  {{ grid-column: span 6; }}
            
            @media (max-width: 900px) {{
                .panel-status, .panel-uptime, .panel-health {{ grid-column: span 12; }}
                .panel-memory, .panel-ports {{ grid-column: span 12; }}
            }}
        </style>
    </head>
    <body>
        <div class="navbar">
            <div style="width: 24px; height: 24px; background: #FF9900; mask-image: url('https://upload.wikimedia.org/wikipedia/commons/3/3b/Grafana_icon.svg'); -webkit-mask-image: url('https://upload.wikimedia.org/wikipedia/commons/3/3b/Grafana_icon.svg'); -webkit-mask-size: contain; mask-size: contain;"></div>
            <h1>Pi5 Monitoring</h1>
            
            <!-- Refresh Control -->
            <select id="refreshInterval" class="refresh-select" onchange="updateRefresh()">
                <option value="5">5s</option>
                <option value="10">10s</option>
                <option value="30">30s</option>
                <option value="60">60s</option>
                <option value="0">Off</option>
            </select>
            
            <div style="margin-left: auto; color: var(--muted); font-size: 12px; display: flex; align-items: center; gap: 8px;">
                <span style="width: 8px; height: 8px; background: {status_color}; border-radius: 50%; display: inline-block;"></span>
                {health['status']}
            </div>
        </div>

        <div class="dashboard-grid">
            <!-- Stat 1: Main Status -->
            <div class="panel panel-status">
                <div class="panel-header">System Status</div>
                <div class="panel-content" style="display: flex; align-items: center; justify-content: center; flex-direction: column;">
                    <div style="font-size: 24px; color: {status_color}; font-weight: 600; margin-bottom: 5px;">
                        {health['status']}
                    </div>
                     <div class="stat-label">Overall Health</div>
                </div>
            </div>

            <!-- Stat 2: Uptime -->
            <div class="panel panel-uptime">
                <div class="panel-header">Uptime</div>
                <div class="panel-content">
                    <div class="stat-value" style="color: var(--green);">{health['uptime']}</div>
                    <div class="stat-label">Since last boot</div>
                </div>
            </div>
            
            <!-- Stat 3: Checks -->
            <div class="panel panel-health">
                <div class="panel-header">Connectivity</div>
                <div class="panel-content">
                     <div style="display: flex; gap: 20px;">
                        <div>
                            <div style="font-size: 18px; color: {'#73BF69' if health['network'] else '#F2495C'}">
                                {"Connected" if health['network'] else "Disconnected"}
                            </div>
                            <div class="stat-label">Network</div>
                        </div>
                        <div>
                            <div style="font-size: 18px; color: {'#73BF69' if health['dns'] else '#F2495C'}">
                                {"Resolved" if health['dns'] else "Failed"}
                            </div>
                            <div class="stat-label">DNS</div>
                        </div>
                     </div>
                </div>
            </div>

            <!-- Panel: Memory -->
            <div class="panel panel-memory">
                <div class="panel-header">Top Memory Processes</div>
                <div class="panel-content">
                    <div class="table-row table-header">
                        <div class="col mono">PID</div>
                        <div class="col">Process</div>
                        <div class="col right">Mem (MB)</div>
                        <div class="col right graph-col"></div>
                    </div>
                    <div class="scroll-list">
                        {proc_rows}
                    </div>
                </div>
            </div>

            <!-- Panel: Ports -->
            <div class="panel panel-ports">
                <div class="panel-header">Listening Ports</div>
                <div class="panel-content">
                    <div class="table-row table-header">
                        <div class="col" style="max-width: 60px;">Proto</div>
                        <div class="col mono">Port</div>
                        <div class="col mono">Addr</div>
                        <div class="col">Scope</div>
                    </div>
                    <div class="scroll-list">
                        {port_rows}
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            const select = document.getElementById("refreshInterval");
            let timer = null;

            // Load saved preference
            const saved = localStorage.getItem("refresh_interval");
            if (saved !== null) {{
                select.value = saved;
            }} else {{
                select.value = "60"; // Default
            }}

            function updateRefresh() {{
                const val = select.value;
                localStorage.setItem("refresh_interval", val);
                
                if (timer) clearTimeout(timer);
                
                if (val !== "0") {{
                    const ms = parseInt(val) * 1000;
                    timer = setTimeout(() => window.location.reload(), ms);
                    console.log("Refreshing in " + ms + "ms");
                }}
            }}

            // Init
            updateRefresh();
        </script>
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
