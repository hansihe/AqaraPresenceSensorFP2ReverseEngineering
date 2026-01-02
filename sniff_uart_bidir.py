# /// script
# dependencies = [
#   "glasgow[builtin-toolchain] @ git+https://github.com/GlasgowEmbedded/glasgow@43f174bf58f3ce05e512be6cd2438c4444f1955b#subdirectory=software"
# ]
# ///

import sys
import logging
import argparse
import asyncio

from glasgow.cli import TerminalFormatter, wait_for_sigint
from glasgow.hardware.device import GlasgowDevice
from glasgow.hardware.assembly import HardwareAssembly
from glasgow.applet import GlasgowAppletMetadata, GlasgowAppletArguments

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

async def main():
    term_handler = create_logger()
    configure_logger(term_handler)

    device = GlasgowDevice(serial=None)
    assembly = HardwareAssembly(device=device)
    
    uart_applet_cls = GlasgowAppletMetadata.get("uart").load()
    
    uart1 = uart_applet_cls(assembly)
    uart1_args = parse_args(uart_applet_cls, ["--rx", "A0", "--tx", "A1", "-V", "3.3", "-b", "890000"])
    uart1.build(uart1_args)
    
    uart2 = uart_applet_cls(assembly)
    uart2_args = parse_args(uart_applet_cls, ["--rx", "A2", "--tx", "A3", "-b", "890000"])
    uart2.build(uart2_args)

    uart3 = uart_applet_cls(assembly)
    uart3_args = parse_args(uart_applet_cls, ["--rx", "A4", "--tx", "A5", "-b", "890000"])
    uart3.build(uart3_args)
    
    async with assembly:
        await uart1.setup(uart1_args)
        await uart2.setup(uart2_args)
        await uart3.setup(uart3_args)

        await inner(uart1, uart2)

async def inner(uart1, uart2):
    async with asyncio.TaskGroup() as group:
        uart1_task = group.create_task(
            applet_task(0, uart1.uart_iface),
            name="uart1"
        )
        uart2_task = group.create_task(
            applet_task(1, uart2.uart_iface),
            name="uart2"
        )
        sigint_task = group.create_task(wait_for_sigint())
        await asyncio.wait([
            uart1_task,
            uart2_task,
            sigint_task
        ])
        sigint_task.cancel()

def format_hex(data):
    return " ".join("{:02x}".format(c) for c in data)

async def applet_task(idx, uart):
    acc = bytes()

    while True:
        data = await uart.read_all()
        if len(data) > 0:
            print(idx, format_hex(bytes(data)))
            #acc = acc + bytes(data)

            #for n in range(1, len(acc)):
            #    if acc[n:n+3] == b"U\x00\x01":
            #        packet = acc[:n]
            #        print(idx, format_hex(packet))

            #        seq = packet[3]
            #        typ = packet[4]
            #        lena = packet[5]
            #        lenb = packet[6]
            #        unk = packet[7]
            #        data = packet[8:lenb+8]
            #        chk = packet[lenb+8:]
            #        print("    seq:{} typ:{} lena:{} lenb:{} unk:{} data:{} chk:{}".format(seq, typ, lena, lenb, unk, format_hex(data), format_hex(chk)))

            #        acc = acc[n:]
            #        break

asyncio.run(main())
