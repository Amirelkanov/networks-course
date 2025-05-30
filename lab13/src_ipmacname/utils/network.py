import socket
import ipaddress
from getmac import get_mac_address
import netifaces
from scapy.all import srp, Ether, ARP


def get_default_interface():
    iface = netifaces.gateways()["default"][netifaces.AF_INET][1]
    addrs = netifaces.ifaddresses(iface)
    info = addrs[netifaces.AF_INET][0]
    return info["addr"], info["netmask"]


def scan_network(
    ip: str,
    netmask: str,
    progress_callback,
    result_callback,
):
    network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)
    hosts = list(network.hosts())
    done, total = 0, len(hosts)

    # Invoke for local PC at first
    result_callback(ip, get_mac_address(ip=ip) or "-", socket.gethostname())

    for host in hosts:
        done += 1
        progress_callback(done, total)

        host = str(host)
        if host == ip:
            continue

        ans, _ = srp(
            Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=host), timeout=1, verbose=0
        )
        if ans:
            _, rcv = ans[0]
            mac = rcv.hwsrc
            try:
                name = socket.gethostbyaddr(host)[0]
            except socket.herror:
                name = "-"
            result_callback(host, mac, name)

    progress_callback(total, total)
