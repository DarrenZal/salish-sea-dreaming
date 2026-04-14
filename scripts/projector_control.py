#!/usr/bin/env python3
"""
projector_control.py — BenQ projector RS232-over-TCP control.

Sends blank/unblank commands to BenQ projectors via their network serial
interface (TCP port 8000). This keeps HDMI alive while hiding the image,
preventing Windows from reshuffling display IDs.

Usage:
    python projector_control.py --blank --ip 192.168.1.X
    python projector_control.py --unblank --ip 192.168.1.X
    python projector_control.py --status --ip 192.168.1.X
    python projector_control.py --scan  # scan local network for BenQ projectors

Deploy to 3090: scp scripts/projector_control.py windows-desktop-remote:C:/Users/user/projector_control.py
"""

import argparse
import socket
import sys
import time


DEFAULT_PORT = 8000
TIMEOUT = 5


def send_command(ip: str, command: str, port: int = DEFAULT_PORT) -> str:
    """Send an RS232 command to BenQ projector and return the response."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIMEOUT)
        sock.connect((ip, port))
        # BenQ RS232 protocol: \r*command#\r
        msg = f"\r*{command}#\r"
        sock.sendall(msg.encode("ascii"))
        time.sleep(0.5)
        response = sock.recv(1024).decode("ascii", errors="replace").strip()
        sock.close()
        return response
    except socket.timeout:
        return "ERROR: Connection timed out"
    except ConnectionRefusedError:
        return "ERROR: Connection refused (port not open)"
    except Exception as e:
        return f"ERROR: {e}"


def blank(ip: str, port: int = DEFAULT_PORT) -> None:
    """Blank the projector image (HDMI stays connected)."""
    print(f"Blanking {ip}:{port}...")
    result = send_command(ip, "blank=on", port)
    print(f"Response: {result}")


def unblank(ip: str, port: int = DEFAULT_PORT) -> None:
    """Restore the projector image."""
    print(f"Unblanking {ip}:{port}...")
    result = send_command(ip, "blank=off", port)
    print(f"Response: {result}")


def get_status(ip: str, port: int = DEFAULT_PORT) -> None:
    """Query projector power status."""
    print(f"Querying {ip}:{port}...")
    result = send_command(ip, "pow=?", port)
    print(f"Power status: {result}")
    result2 = send_command(ip, "blank=?", port)
    print(f"Blank status: {result2}")


def scan_network(subnet: str = "192.168.1") -> None:
    """Scan local network for devices with port 8000 open (likely BenQ projectors)."""
    print(f"Scanning {subnet}.1-254 for port {DEFAULT_PORT}...")
    found = []
    for i in range(1, 255):
        ip = f"{subnet}.{i}"
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            result = sock.connect_ex((ip, DEFAULT_PORT))
            sock.close()
            if result == 0:
                print(f"  FOUND: {ip}:{DEFAULT_PORT} open")
                found.append(ip)
        except Exception:
            pass
    if not found:
        print("No devices found with port 8000 open.")
    else:
        print(f"\nFound {len(found)} device(s): {', '.join(found)}")
    return found


def main():
    parser = argparse.ArgumentParser(description="BenQ projector RS232-over-TCP control")
    parser.add_argument("--ip", type=str, help="Projector IP address")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"TCP port (default: {DEFAULT_PORT})")
    parser.add_argument("--blank", action="store_true", help="Blank the projector image")
    parser.add_argument("--unblank", action="store_true", help="Restore the projector image")
    parser.add_argument("--status", action="store_true", help="Query projector status")
    parser.add_argument("--scan", action="store_true", help="Scan local network for BenQ projectors")
    parser.add_argument("--subnet", type=str, default="192.168.1", help="Subnet to scan (default: 192.168.1)")
    args = parser.parse_args()

    if args.scan:
        scan_network(args.subnet)
        return

    if not args.ip:
        parser.error("--ip is required for blank/unblank/status commands")

    if args.blank:
        blank(args.ip, args.port)
    elif args.unblank:
        unblank(args.ip, args.port)
    elif args.status:
        get_status(args.ip, args.port)
    else:
        parser.error("Specify --blank, --unblank, --status, or --scan")


if __name__ == "__main__":
    main()
