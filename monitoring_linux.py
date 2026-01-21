
import subprocess
import socket
import time
from util import classify_scope

def get_listening_ports():
    cmd = "ss -tulnpH | grep LISTEN"
    result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
    listeners = []

    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5: continue
        proto = parts[0]
        local = parts[4]

        # Handle IPv6 [::]:22
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

    listeners.sort(key=lambda x: x["port"])
    return listeners

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
    # Linux: -W 1 (1 second)
    res = subprocess.run(["ping", "-c", "1", "-W", "1", "8.8.8.8"], stdout=subprocess.DEVNULL)
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
        cmd = "ps axo pid,comm,rss --sort=-rss | head -n 6"
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
