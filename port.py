import psutil, shutil, subprocess, time, sys

WEB_PORTS = {80, 443, 5000, 8000}  # restrict to webapp ports
known_ports = set()

iptables = shutil.which("iptables")
nft = shutil.which("nft")

if not iptables and not nft:
    print("[-] Neither iptables nor nftables found. Install one of them.")
    sys.exit(1)

def run_cmd(cmd):
    try:
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass  # ignore errors like "rule not found"

def open_port(port):
    if iptables:
        run_cmd([iptables, "-C", "INPUT", "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"]) or \
        run_cmd([iptables, "-A", "INPUT", "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"])
        print(f"[+] Opened port {port} via iptables")
    elif nft:
        run_cmd([nft, "add", "rule", "inet", "filter", "input", "tcp", "dport", str(port), "accept"])
        print(f"[+] Opened port {port} via nftables")

def close_port(port):
    if iptables:
        run_cmd([iptables, "-D", "INPUT", "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"])
        print(f"[-] Closed port {port} via iptables")
    elif nft:
        run_cmd([nft, "delete", "rule", "inet", "filter", "input", "tcp", "dport", str(port), "accept"])
        print(f"[-] Closed port {port} via nftables")

def get_active_ports():
    return {c.laddr.port for c in psutil.net_connections(kind='inet') if c.status == 'LISTEN'}

while True:
    active = get_active_ports() & WEB_PORTS
    
    for port in active - known_ports:
        open_port(port)
    for port in known_ports - active:
        close_port(port)
    
    known_ports = active
    time.sleep(5)
