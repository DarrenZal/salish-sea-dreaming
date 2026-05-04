import socket
import struct

addr = b'/composition/tempocontroller/tempo'
addr += b'\x00' * (4 - len(addr) % 4 if len(addr) % 4 else 4)
types = b',f\x00\x00'
val = struct.pack('>f', 128.0)
pkt = addr + types + val

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(pkt, ('127.0.0.1', 7001))
print(f'sent {len(pkt)} bytes to 127.0.0.1:7001')
print(f'packet hex: {pkt.hex()}')
