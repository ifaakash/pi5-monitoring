
import sys
import os
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

print("--- Testing html-dashboard.py ---")
try:
    html_dashboard = import_file("html_dashboard", "/Users/aakashmac/DevOps/Github/pi5-monitoring/html-dashboard.py")
    listeners = html_dashboard.get_listening_ports()
    print(f"Found {len(listeners)} ports.")
    for l in listeners:
        print(l)
except Exception as e:
    print(f"Error: {e}")

print("\n--- Testing monitoring.py ---")
try:
    monitoring = import_file("monitoring", "/Users/aakashmac/DevOps/Github/pi5-monitoring/monitoring.py")
    listeners = monitoring.get_listening_ports()
    print(f"Found {len(listeners)} ports.")
    for l in listeners:
        print(l)
except Exception as e:
    print(f"Error: {e}")
