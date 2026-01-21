
import subprocess
import re
import socket
import time
from util import classify_scope

def get_listening_ports():
    listeners = []
    cmd = "lsof -i -P -n | grep LISTEN"
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 9: continue
        
        # Format: COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME (STATE)
        address = parts[-2]
        proto = parts[-3].lower()
        family = parts[4].lower()
        
        if ":" in address:
            ip_port = address.rsplit(":", 1)
            ip = ip_port[0]
            port = ip_port[1]
            if ip == "*": ip = "0.0.0.0" if family == "ipv4" else "::"
            
            listeners.append({
                "protocol": proto,
                "ip": ip,
                "port": int(port),
                "family": family,
                "scope": classify_scope(ip)
            })
            
    listeners.sort(key=lambda x: x["port"])
    return listeners

def get_uptime():
    try:
        cmd = "sysctl -n kern.boottime"
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        match = re.search(r"sec = (\d+)", result.stdout)
        if match:
            boot_time = int(match.group(1))
            seconds = time.time() - boot_time
        else:
            seconds = 0
            
        minutes = int(seconds // 60)
        hours = minutes // 60
        days = hours // 24
        return f"{int(days)}d {int(hours % 24)}h {int(minutes % 60)}m"
    except Exception as e:
        print(f"Error uptime: {e}")
        return "Unknown"

def check_network():
    # macOS: -W 1000 (1000 ms)
    res = subprocess.run(["ping", "-c", "1", "-W", "1000", "8.8.8.8"], stdout=subprocess.DEVNULL)
    return res.returncode == 0

def check_dns():
    try:
        socket.setdefaulttimeout(1)
        socket.gethostbyname("google.com")
        return True
    except:
        return False

def get_top_processes():
    processes = []
    try:
        cmd = "ps -caxm -o pid,comm,rss | head -n 6"
        result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        lines = result.stdout.strip().splitlines()
        
        if len(lines) > 0:
            for line in lines[1:]:
                parts = line.split()
                if len(parts) >= 3:
                    pid = parts[0]
                    rss = parts[-1]
                    comm = " ".join(parts[1:-1])
                    try:
                        rss_mb = round(int(rss) / 1024, 1)
                    except:
                        rss_mb = 0
                    processes.append({"pid": pid, "name": comm, "memory_mb": rss_mb})
    except Exception as e:
        print(f"Error processes: {e}")
    return processes
