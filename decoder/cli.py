import argparse
import sys
from .framer import Framer
from .protocol import decode_packet

def parse_line_generator(filename):
    """Generator that yields (channel, data_bytes) tuples from a file."""
    try:
        with open(filename, "r") as f:
            for line in f:
                items = line.strip().split(" ")
                if not items:
                    continue
                # Auto-detect timestamp and ignore it
                if items[0].startswith("t"):
                    items.pop(0)
                    if not items:
                        continue
                
                try:
                    channel = int(items[0])
                    # Optimized hex parsing
                    dps_bytes = bytearray(int(x, 16) for x in items[1:])
                    yield channel, dps_bytes
                except ValueError:
                    continue
    except FileNotFoundError:
        print(f"File not found: {filename}")
        return

def handle_decode(args):
    print(f"\n{'='*20} {args.file} {'='*20}")
    
    framers = [Framer(0), Framer(1)]
    
    # Callback to print packets as they are framed
    # Callback to print packets as they are framed
    def print_packet(channel, packet):
        lines = decode_packet(channel, packet, exclude_names=args.exclude)
        for line in lines:
            print(line)

    for channel, data in parse_line_generator(args.file):
        framers[channel].add(data)
        while framers[channel].packets:
            packet = framers[channel].packets.pop(0)
            print_packet(channel, packet)

def handle_sniff(args):
    from .sniffer import run_sniffer
    run_sniffer(args)

def main():
    parser = argparse.ArgumentParser(description="Aqara FP2 Protocol Decoder")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Decode subcommand
    decode_parser = subparsers.add_parser("decode", help="Decode a capture file")
    decode_parser.add_argument("file", help="Path to the capture file")
    decode_parser.add_argument("--exclude", "-x", help="Exclude attributes by name (comma separated)", type=lambda s: s.split(","))
    decode_parser.set_defaults(func=handle_decode)

    # Sniff subcommand
    sniff_parser = subparsers.add_parser("sniff", help="Sniff UART in real-time (requires Glasgow)")
    sniff_parser.add_argument("--out", "-o", help="Output file for raw capture", default=None)
    sniff_parser.add_argument("--exclude", "-x", help="Exclude attributes by name (comma separated)", type=lambda s: s.split(","))
    sniff_parser.add_argument("--visualize", "-v", help="Open visualization window for target positions", action="store_true")
    # Add Glasgow args if needed, or pass them through
    sniff_parser.set_defaults(func=handle_sniff)

    args = parser.parse_args()
    args.func(args)
