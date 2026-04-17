"""gallery_resolume_refresh.py -- OSC-based Resolume output refresh.

Sends OSC messages to force Arena to re-validate and re-engage its screen
outputs. Equivalent to Prav's manual "open Advanced Output panel" morning
fix, without the Windows foreground-lock games that defeat SendKeys.

Mechanism: toggle each screen's `bypassed` flag on briefly, then off. Arena
responds by tearing down and re-establishing the output pipeline, which is
what actually restores the projectors after a cold boot.

Run locally on the 3090 (OSC is localhost-only by default):

    python gallery_resolume_refresh.py                  # toggles screens 1-2
    python gallery_resolume_refresh.py --screens 1 2 3  # explicit screen IDs
    python gallery_resolume_refresh.py --host 127.0.0.1 --port 7001
    python gallery_resolume_refresh.py --dry-run        # print only

Run remotely via SSH from anywhere:

    ssh windows-desktop-remote "python C:\\Users\\user\\gallery_resolume_refresh.py"
"""
import argparse
import socket
import struct
import sys
import time


def pad_osc_string(s: str) -> bytes:
    """Encode an OSC string: UTF-8 bytes + 1-4 null bytes to 4-byte align."""
    b = s.encode('utf-8')
    pad = 4 - (len(b) % 4)
    return b + b'\x00' * pad


def osc_pack(address: str, *args) -> bytes:
    """Pack a single OSC message. Supports int and float args."""
    packet = pad_osc_string(address)
    type_tag = ','
    values = b''
    for a in args:
        if isinstance(a, int):
            type_tag += 'i'
            values += struct.pack('>i', a)
        elif isinstance(a, float):
            type_tag += 'f'
            values += struct.pack('>f', a)
        else:
            raise TypeError(f'Unsupported OSC arg type: {type(a)}')
    packet += pad_osc_string(type_tag)
    packet += values
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='127.0.0.1',
                        help='Arena OSC input host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=7001,
                        help='Arena OSC input port (default: 7001)')
    parser.add_argument('--screens', type=int, nargs='+', default=[1, 2],
                        help='Screen IDs to toggle (default: 1 2)')
    parser.add_argument('--dwell-ms', type=int, default=300,
                        help='How long to hold bypass=1 before releasing (default: 300ms)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print what would be sent without sending')
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(address, value):
        packet = osc_pack(address, value)
        prefix = '[DRY]' if args.dry_run else '[OSC]'
        print(f'{prefix} {address} -> {value}   ({len(packet)} bytes)')
        if not args.dry_run:
            sock.sendto(packet, (args.host, args.port))

    print(f'Refreshing Resolume screens {args.screens} via {args.host}:{args.port}')

    for screen_id in args.screens:
        send(f'/composition/screens/{screen_id}/bypassed', 1)

    if not args.dry_run:
        time.sleep(args.dwell_ms / 1000.0)

    for screen_id in args.screens:
        send(f'/composition/screens/{screen_id}/bypassed', 0)

    print('Done')
    return 0


if __name__ == '__main__':
    sys.exit(main())
