import netifaces
import argparse
from typing import List, Tuple


def get_ip_and_mask(all_interfaces=False) -> List[Tuple[str, str, str]]:
    iface_ip_mask: List[Tuple[str, str, str]] = []

    default_interface = netifaces.gateways()["default"][netifaces.AF_INET][1]
    interfaces = netifaces.interfaces() if all_interfaces else [default_interface]
    for iface in interfaces:
        addrs = netifaces.ifaddresses(iface)
        ipv4 = addrs.get(netifaces.AF_INET)
        if not ipv4:
            continue
        for link in ipv4:
            iface_ip_mask.append((iface, link.get("addr"), link.get("netmask")))
    return iface_ip_mask


def main():
    parser = argparse.ArgumentParser(
        "Get IP address and netmask in following format:\n<interface>\tIP: <ip> Netmask: <mask>"
    )
    parser.add_argument(
        "-a", "--all-interfaces", action="store_true", help="show for all interfaces"
    )
    args = parser.parse_args()
    for iface, ip, mask in get_ip_and_mask(all_interfaces=args.all_interfaces):
        print(f"{iface}\tIP: {ip}  Netmask: {mask}")


if __name__ == "__main__":
    main()
