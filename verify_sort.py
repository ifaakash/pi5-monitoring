
import subprocess
import sys
import os
import importlib.util

# Mocking subprocess before import
from unittest.mock import MagicMock
import subprocess

# Mock result with mixed up ports
mock_stdout = """
udp   UNCONN 0      0            0.0.0.0:5353       0.0.0.0:*
tcp   LISTEN 0      4096         0.0.0.0:8000       0.0.0.0:*
tcp   LISTEN 0      128          0.0.0.0:22         0.0.0.0:*
tcp   LISTEN 0      4096            [::]:443           [::]:*
"""

original_run = subprocess.run
def side_effect(*args, **kwargs):
    if "ss -tulnpH" in args[0]:
        return MagicMock(stdout=mock_stdout)
    return original_run(*args, **kwargs)

subprocess.run = MagicMock(side_effect=side_effect)

def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

print("--- Testing html-dashboard.py ---")
html_dashboard = import_file("html_dashboard", "/Users/aakashmac/DevOps/Github/pi5-monitoring/html-dashboard.py")
listeners = html_dashboard.get_listening_ports()
print("Ports:", [l['port'] for l in listeners])
is_sorted = all(listeners[i]['port'] <= listeners[i+1]['port'] for i in range(len(listeners)-1))
print(f"Sorted: {is_sorted}")

print("\n--- Testing monitoring.py ---")
monitoring = import_file("monitoring", "/Users/aakashmac/DevOps/Github/pi5-monitoring/monitoring.py")
listeners2 = monitoring.get_listening_ports()
print("Ports:", [l['port'] for l in listeners2])
is_sorted2 = all(listeners2[i]['port'] <= listeners2[i+1]['port'] for i in range(len(listeners2)-1))
print(f"Sorted: {is_sorted2}")
