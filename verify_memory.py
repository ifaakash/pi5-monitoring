
import sys
import importlib.util
import platform
import subprocess

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
    procs = monitoring.get_top_processes()
    print(f"Found {len(procs)} processes.")
    for p in procs:
        print(p)
        
    health = monitoring.get_health()
    print("Health keys:", health.keys())
    if "processes" in health:
        print("Processes included in health check: Yes")
    else:
        print("Processes included in health check: NO")

except Exception as e:
    print(f"Error: {e}")

print("\n--- Testing html-dashboard.py ---")
try:
    html_dashboard = import_file("html_dashboard", "/Users/aakashmac/DevOps/Github/pi5-monitoring/html-dashboard.py")
    procs = html_dashboard.get_top_processes()
    print(f"Found {len(procs)} processes.")
    for p in procs:
        print(p)
except Exception as e:
    print(f"Error: {e}")
