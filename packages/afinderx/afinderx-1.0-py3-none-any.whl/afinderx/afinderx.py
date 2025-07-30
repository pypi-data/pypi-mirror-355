import socket
from ipaddress import ip_network
from datetime import datetime

def scan_ip_port(ip, port=5555):
    try:
        sock = socket.socket()
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        if result == 0:
            return "open"
        else:
            return "closed"
    except Exception:
        return "error"
    finally:
        sock.close()

def main():
    print("Android Port Scanner - afinderx")
    ip_range = input("Enter IP range (e.g., 192.168.0.0/24): ").strip()

    network = ip_network(ip_range, strict=False)
    port = 5555
    open_ips = []
    closed_ips = []

    print(f"\nScanning port {port} on {ip_range}...\n")

    for ip in network.hosts():
        status = scan_ip_port(str(ip), port)
        if status == "open":
            print(f"[OPEN]     {ip} target is open")
            open_ips.append(str(ip))
        elif status == "closed":
            closed_ips.append(str(ip))

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"afinderx_output_{now}_{ip_range.replace('/', '_')}.txt"

    with open(output_filename, "w") as f:
        f.write("==== Open IPs ====\n")
        for ip in open_ips:
            f.write(f"{ip}\n")
        f.write("\n==== Closed IPs ====\n")
        for ip in closed_ips:
            f.write(f"{ip}\n")

    print(f"\nScan complete. Results saved to {output_filename}")
