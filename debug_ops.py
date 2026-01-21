
import subprocess
import socket
import time
import platform

def check_network():
    # Detect OS for correct ping timeout syntax
    # Linux: -W 1 (1 second)
    # macOS: -W 1000 (1000 milliseconds)
    param = "-W"
    system = platform.system().lower()
    if system == "darwin":
        timeout = "1000" 
    else:
        timeout = "1"
    
    print(f"OS Detection: {system}, checking with timeout {timeout}")

    # Reduced count and wait time for speed
    start = time.time()
    res = subprocess.run(["ping", "-c", "1", param, timeout, "8.8.8.8"], stdout=subprocess.DEVNULL)
    end = time.time()
    print(f"check_network: returncode={res.returncode}, time={end-start:.4f}s")
    return res.returncode == 0

def check_dns():
    try:
        socket.setdefaulttimeout(1)
        start = time.time()
        socket.gethostbyname("google.com")
        end = time.time()
        print(f"check_dns: Success, time={end-start:.4f}s")
        return True
    except Exception as e:
        print(f"check_dns: Failed ({e})")
        return False

print("Running checks with fix...")
net = check_network()
dns = check_dns()
print(f"Network: {net}")
print(f"DNS: {dns}")

if net and dns: status = "Online"
elif net and not dns: status = "DNS Error"
else: status = "Offline"
print(f"Resulting Status: {status}")
