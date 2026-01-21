
import sys
import importlib.util
import platform
import subprocess
import time

print(f"Running on: {platform.system()}")

def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

print("--- Testing monitoring.py ---")
try:
    monitoring = import_file("monitoring", "/Users/aakashmac/DevOps/Github/pi5-monitoring/monitoring.py")
    uptime = monitoring.get_uptime()
    print(f"Uptime: {uptime}")
    if isinstance(uptime, str) and uptime != "Unknown":
        print("Uptime check passed")
    else:
        print("WARNING: Uptime unexpected format/value")
        
    procs = monitoring.get_top_processes()
    print(f"Found {len(procs)} processes")

except Exception as e:
    print(f"Error: {e}")

print("\n--- Testing html-dashboard.py ---")
try:
    html_dashboard = import_file("html_dashboard", "/Users/aakashmac/DevOps/Github/pi5-monitoring/html-dashboard.py")
    # html-dashboard now delegates to monitoring, so we just check if it imports and render_html works
    print("Imports successful.")
    
    # Test render_html if possible, or just trust monitoring tests
    # Mock data
    health = {"uptime": "1d 2h", "status": "Online", "network": True, "dns": True, "processes": []}
    ports = []
    html = html_dashboard.render_html(health, ports)
    if "1d 2h" in html:
        print("render_html check passed")
    else:
        print("render_html check FAILED")
    
except Exception as e:
    print(f"Error: {e}")
