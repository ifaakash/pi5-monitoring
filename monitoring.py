
import platform
import sys

# Select backend based on OS
if platform.system() == "Darwin":
    import monitoring_darwin as backend
else:
    import monitoring_linux as backend

# Expose backend functions directly
get_listening_ports = backend.get_listening_ports
get_uptime = backend.get_uptime
check_network = backend.check_network
check_dns = backend.check_dns
get_top_processes = backend.get_top_processes

def network_status():
    network_ok = check_network()
    dns_ok = check_dns()

    if network_ok and dns_ok:
        status = "Online"
    elif network_ok and not dns_ok:
        status = "DNS Error"
    else:
        status = "Offline"

    return {
        "network": network_ok,
        "dns": dns_ok,
        "status": status
    }

def get_health():
    net_stat = network_status()
    return {
        "uptime": get_uptime(),
        "network": net_stat["network"],
        "dns": net_stat["dns"],
        "status": net_stat["status"],
        "processes": get_top_processes()
    }

# Main execution for testing
if __name__ == "__main__":
    print("Health Check:")
    print(get_health())
    print("\nPorts:")
    print(get_listening_ports())
