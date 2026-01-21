
def classify_scope(ip):
    if ip.startswith("127.") or ip == "::1": return "Localhost"
    if ip == "0.0.0.0" or ip == "::": return "All Interfaces"
    if ip.startswith("192.168.") or ip.startswith("10."): return "LAN"
    return "Public"
