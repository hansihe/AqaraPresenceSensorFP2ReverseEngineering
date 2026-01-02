import sys
import logging
import argparse
import asyncio
import time
import struct
from datetime import datetime

from glasgow.cli import TerminalFormatter, wait_for_sigint
from glasgow.hardware.device import GlasgowDevice
from glasgow.hardware.assembly import HardwareAssembly
from glasgow.applet import GlasgowAppletMetadata, GlasgowAppletArguments

from .framer import Framer
from .protocol import decode_packet

def parse_args(applet_cls, args):
    applet_parser = argparse.ArgumentParser()
    applet_parsed_args = applet_parser.parse_args([])
    applet_cls.add_build_arguments(applet_parser,
        GlasgowAppletArguments("name"))
    applet_cls.add_setup_arguments(applet_parser)
    applet_cls.add_run_arguments(applet_parser)
    return applet_parser.parse_args(args)

def create_logger():
    root_logger = logging.getLogger()

    term_formatter_args = {"style": "{",
        "fmt": "{levelname[0]:s}: {name:s}: {message:s}"}
    term_handler = logging.StreamHandler()
    if sys.stderr.isatty() and sys.platform != 'win32':
        term_handler.setFormatter(TerminalFormatter(**term_formatter_args))
    else:
        term_handler.setFormatter(logging.Formatter(**term_formatter_args))
    root_logger.addHandler(term_handler)
    return term_handler

def configure_logger(term_handler):
    root_logger = logging.getLogger()

    file_formatter_args = {"style": "{",
        "fmt": "[{asctime:s}] {levelname:s}: {name:s}: {message:s}"}
    file_handler = None

    level = logging.INFO
    root_logger.setLevel(level)

def extract_targets_from_packet(packet):
    """Extract target position data from location_track_data packets.

    Returns:
        List of tuples (tid, x, y, z, velocity, snr, classifier, posture, active) or None
    """
    # Check if this is a location_track_data report (0x0117, type 5)
    if len(packet.data) < 2:
        return None

    sub_id = packet.data[0] << 8 | packet.data[1]
    if sub_id != 0x0117 or packet.typ != 5:
        return None

    # Parse the target data
    if len(packet.data) < 5:
        return None

    sub_data_len = packet.data[3] << 8 | packet.data[4]
    sub_data = packet.data[5:5+sub_data_len]

    if len(sub_data) == 0:
        return None

    count = sub_data[0]
    targets = []

    for n in range(count):
        item_data = sub_data[1+(14*n):1+(14*(n+1))]
        if len(item_data) == 14:
            tid, x, y, z, velocity, snr, classifier, posture, active = struct.unpack(">BhhhhHBBB", item_data)
            targets.append((tid, x, y, z, velocity, snr, classifier, posture, active))

    return targets if targets else None

async def applet_task(idx, uart, outfile, framer, exclude_names=None, visualizer=None):
    while True:
        data = await uart.read_all()
        if len(data) > 0:
            ts = time.time()
            hex_data = " ".join("{:02x}".format(c) for c in data)
            line = f"t{ts:.3f} {idx} {hex_data}"

            # Write raw log
            if outfile:
                outfile.write(line + "\n")
                outfile.flush()

            # Feed framer
            framer.add(data)

            # Process packets immediately
            while framer.packets:
                packet = framer.packets.pop(0)
                lines = decode_packet(idx, packet, exclude_names=exclude_names)
                for l in lines:
                    print(l)

                # Update visualizer if enabled
                if visualizer:
                    targets = extract_targets_from_packet(packet)
                    if targets:
                        visualizer.update_targets(targets)

async def inner(uart1, uart2, outfile, exclude_names=None, visualizer=None):
    framers = [Framer(0), Framer(1)]

    async with asyncio.TaskGroup() as group:
        uart1_task = group.create_task(
            applet_task(0, uart1.uart_iface, outfile, framers[0], exclude_names, visualizer),
            name="uart1"
        )
        uart2_task = group.create_task(
            applet_task(1, uart2.uart_iface, outfile, framers[1], exclude_names, visualizer),
            name="uart2"
        )
        sigint_task = group.create_task(wait_for_sigint())
        await asyncio.wait([
            uart1_task,
            uart2_task,
            sigint_task
        ])
        sigint_task.cancel()

async def main(args):
    term_handler = create_logger()
    configure_logger(term_handler)

    # Initialize visualizer if requested
    visualizer = None
    if args.visualize:
        from .visualizer import TargetVisualizer
        visualizer = TargetVisualizer()
        visualizer.start()
        print("Visualization window started")

    device = GlasgowDevice(serial=None)
    assembly = HardwareAssembly(device=device)

    uart_applet_cls = GlasgowAppletMetadata.get("uart").load()

    uart1 = uart_applet_cls(assembly)
    uart1_args = parse_args(uart_applet_cls, ["--rx", "A0", "--tx", "A1", "-V", "3.3", "-b", "890000"])
    uart1.build(uart1_args)

    uart2 = uart_applet_cls(assembly)
    uart2_args = parse_args(uart_applet_cls, ["--rx", "A2", "--tx", "A3", "-b", "890000"])
    uart2.build(uart2_args)

    filename = args.out
    outfile = None

    if filename:
        print(f"Writing raw capture to: {filename}")
        outfile = open(filename, "w")
    else:
        # Auto-generate if not desired? Or strictly follow arg?
        # Original script auto-generated. Let's start with auto-generate if not provided?
        # Actually CLI default is None. Let's auto-generate if None to be safe.
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sniff_data_{timestamp}.txt"
        print(f"Writing raw capture to: {filename}")
        outfile = open(filename, "w")

    try:
        async with assembly:
            await uart1.setup(uart1_args)
            await uart2.setup(uart2_args)

            await inner(uart1, uart2, outfile, args.exclude, visualizer)
    finally:
        if outfile:
            outfile.close()
        if visualizer:
            visualizer.stop()

def run_sniffer(args):
    try:
        asyncio.run(main(args))
    except ImportError:
        print("Glasgow dependencies not found. Please install glasgow.")
