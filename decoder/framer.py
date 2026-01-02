from dataclasses import dataclass
from .crc import calc_crc

@dataclass
class FramedPacket:
    seq: int
    typ: int
    data: bytearray
    raw: bytearray

MAX_BUF_SIZE = 128 * 1024  # 128KB buffer limit
XMODEM_SOH = 0x01
XMODEM_STX = 0x02
XMODEM_EOT = 0x04
XMODEM_ACK = 0x06
XMODEM_NAK = 0x15
XMODEM_CAN = 0x18

class Framer:
    def __init__(self, channel, on_drop=None, on_xmodem_block=None):
        self.channel = channel
        self.acc = bytearray()
        self.packets = []
        self.in_xmodem = False
        self.last_xmodem_seq = None
        self.on_drop_cb = on_drop
        self.on_xmodem_block_cb = on_xmodem_block

    def on_drop(self, data, reason):
        if self.on_drop_cb:
            self.on_drop_cb(self.channel, data, reason)

    def add(self, data):
        # Prevent unbounded growth
        if len(self.acc) > MAX_BUF_SIZE:
             # Drop old data if buffer is too full to prevent OOM/slowdown
             # Keep last 4KB to maintain context
             drop_len = len(self.acc) - 4096
             self.on_drop(self.acc[:drop_len], "buffer_overflow")
             self.acc = self.acc[-4096:]
        
        self.acc.extend(data)
        self.decode_all()

    def decode_all(self):
        while True:
            # Find earliest Standard Header
            idx_55 = self.acc.find(b"\x55\x00\x01")
            
            # Find earliest XMODEM Header (SOH/STX) with valid Seq structure
            idx_xm = -1
            xm_type = 0
            
            # Helper to find valid XMODEM start
            def find_valid_xm(start_byte_val, byte_type):
                offset = 0
                while True:
                    idx = self.acc.find(bytes([start_byte_val]), offset)
                    if idx == -1: return -1, None
                    
                    # Check XMODEM Header structure: [Type] [Seq] [~Seq]
                    if idx + 3 <= len(self.acc):
                        seq = self.acc[idx+1]
                        seq_inv = self.acc[idx+2]
                        if (seq + seq_inv) & 0xFF == 0xFF:
                             return idx, byte_type
                    offset = idx + 1
                return -1, None

            # Search for SOH and STX
            idx_soh, _ = find_valid_xm(XMODEM_SOH, XMODEM_SOH)
            idx_stx, _ = find_valid_xm(XMODEM_STX, XMODEM_STX)
            
            # Pick best XMODEM candidate (earliest)
            if idx_soh != -1 and (idx_stx == -1 or idx_soh < idx_stx):
                idx_xm = idx_soh
                xm_type = XMODEM_SOH
            elif idx_stx != -1:
                idx_xm = idx_stx
                xm_type = XMODEM_STX
                
            # Determine which header comes first (Standard vs XMODEM)
            # Use a large number for "not found" to simplify min() logic
            pos_55 = idx_55 if idx_55 != -1 else float('inf')
            pos_xm = idx_xm if idx_xm != -1 else float('inf')
            
            best_start = min(pos_55, pos_xm)
            
            if best_start == float('inf'):
                # No headers found
                break
                
            # If we found something, but it's not at 0, drop garbage
            if best_start > 0:
                self.on_drop(self.acc[:best_start], "garbage_before_header")
                self.acc = self.acc[best_start:]
                # Re-evaluate from 0
                continue
                
            # Now self.acc[0] is a valid header candidate
            
            # Case 1: XMODEM
            if pos_xm == 0:
                 # Re-validate to be sure (since we might have just shifted)
                 # Structure: [Type] [Seq] [~Seq] ...
                 # Check length
                 block_len = 128 if xm_type == XMODEM_SOH else 1024
                 overhead = 3 # Head, Seq, ~Seq
                 total_len = overhead + block_len + 2 # +2 for CRC
                 
                 if len(self.acc) < total_len:
                     # Wait for more data
                     break
                 
                 # Verify Seq again just in case
                 seq = self.acc[1]
                 
                 # Check for gaps
                 if self.last_xmodem_seq is not None:
                     expected_seq = (self.last_xmodem_seq + 1) & 0xFF
                     if seq != expected_seq and seq != self.last_xmodem_seq: # Ignore duplicates if any
                         pass # Warning is handled by the caller/logger if needed, or we can add a callback
                 
                 self.last_xmodem_seq = seq
                 
                 # Consume
                 if self.on_xmodem_block_cb:
                     self.on_xmodem_block_cb(self.channel, seq, block_len)
                 
                 self.acc = self.acc[total_len:]
                 continue
            # Case 2: Standard Protocol (0x55 0x01...)
            # We already know acc[0:3] == 55 00 01 because of the find + shift logic
            if len(self.acc) < 8:
                break

            bsum = -1
            for d in self.acc[:7]:
                bsum += d
            bsum = bsum & 0xff
            calc_hdr_chk = bsum ^ 0xff 
            data_hdr_chk = self.acc[7]
            if calc_hdr_chk != data_hdr_chk:
                self.on_drop(self.acc[:3], "bad header parity digit ({} != {})".format(data_hdr_chk, calc_hdr_chk))
                self.acc = self.acc[3:]
                continue # Retry from new start

            dlen = self.acc[5] << 8 | self.acc[6]
            if len(self.acc) < 8 + dlen + 2:
                break

            data_crc = self.acc[8+dlen:8+dlen+2]
            calced_crc = calc_crc(self.acc[:8 + dlen])
            if data_crc != calced_crc:
                self.on_drop(self.acc[:3], "bad crc ({} != {})".format(data_crc.hex(), calced_crc.hex()))
                self.acc = self.acc[3:]
                continue

            seq = self.acc[3]
            typ = self.acc[4]
            data = self.acc[8:8+dlen]
            packet = FramedPacket(
                raw=self.acc[:8+dlen+2],
                seq=seq,
                typ=typ,
                data=data,
            )

            self.acc = self.acc[8+dlen+2:]

            self.packets.append(packet)
