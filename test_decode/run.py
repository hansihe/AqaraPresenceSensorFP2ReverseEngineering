# /// script
# dependencies = [
# ]
# ///

from dataclasses import dataclass

def format_hex(data):
    return " ".join("{:02x}".format(c) for c in data)

aucCRCHi = [
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x00, 0xC1, 0x81, 0x40,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40, 0x01, 0xC0, 0x80, 0x41, 0x01, 0xC0, 0x80, 0x41,
    0x00, 0xC1, 0x81, 0x40
]

aucCRCLo = [
    0x00, 0xC0, 0xC1, 0x01, 0xC3, 0x03, 0x02, 0xC2, 0xC6, 0x06, 0x07, 0xC7,
    0x05, 0xC5, 0xC4, 0x04, 0xCC, 0x0C, 0x0D, 0xCD, 0x0F, 0xCF, 0xCE, 0x0E,
    0x0A, 0xCA, 0xCB, 0x0B, 0xC9, 0x09, 0x08, 0xC8, 0xD8, 0x18, 0x19, 0xD9,
    0x1B, 0xDB, 0xDA, 0x1A, 0x1E, 0xDE, 0xDF, 0x1F, 0xDD, 0x1D, 0x1C, 0xDC,
    0x14, 0xD4, 0xD5, 0x15, 0xD7, 0x17, 0x16, 0xD6, 0xD2, 0x12, 0x13, 0xD3,
    0x11, 0xD1, 0xD0, 0x10, 0xF0, 0x30, 0x31, 0xF1, 0x33, 0xF3, 0xF2, 0x32,
    0x36, 0xF6, 0xF7, 0x37, 0xF5, 0x35, 0x34, 0xF4, 0x3C, 0xFC, 0xFD, 0x3D,
    0xFF, 0x3F, 0x3E, 0xFE, 0xFA, 0x3A, 0x3B, 0xFB, 0x39, 0xF9, 0xF8, 0x38,
    0x28, 0xE8, 0xE9, 0x29, 0xEB, 0x2B, 0x2A, 0xEA, 0xEE, 0x2E, 0x2F, 0xEF,
    0x2D, 0xED, 0xEC, 0x2C, 0xE4, 0x24, 0x25, 0xE5, 0x27, 0xE7, 0xE6, 0x26,
    0x22, 0xE2, 0xE3, 0x23, 0xE1, 0x21, 0x20, 0xE0, 0xA0, 0x60, 0x61, 0xA1,
    0x63, 0xA3, 0xA2, 0x62, 0x66, 0xA6, 0xA7, 0x67, 0xA5, 0x65, 0x64, 0xA4,
    0x6C, 0xAC, 0xAD, 0x6D, 0xAF, 0x6F, 0x6E, 0xAE, 0xAA, 0x6A, 0x6B, 0xAB,
    0x69, 0xA9, 0xA8, 0x68, 0x78, 0xB8, 0xB9, 0x79, 0xBB, 0x7B, 0x7A, 0xBA,
    0xBE, 0x7E, 0x7F, 0xBF, 0x7D, 0xBD, 0xBC, 0x7C, 0xB4, 0x74, 0x75, 0xB5,
    0x77, 0xB7, 0xB6, 0x76, 0x72, 0xB2, 0xB3, 0x73, 0xB1, 0x71, 0x70, 0xB0,
    0x50, 0x90, 0x91, 0x51, 0x93, 0x53, 0x52, 0x92, 0x96, 0x56, 0x57, 0x97,
    0x55, 0x95, 0x94, 0x54, 0x9C, 0x5C, 0x5D, 0x9D, 0x5F, 0x9F, 0x9E, 0x5E,
    0x5A, 0x9A, 0x9B, 0x5B, 0x99, 0x59, 0x58, 0x98, 0x88, 0x48, 0x49, 0x89,
    0x4B, 0x8B, 0x8A, 0x4A, 0x4E, 0x8E, 0x8F, 0x4F, 0x8D, 0x4D, 0x4C, 0x8C,
    0x44, 0x84, 0x85, 0x45, 0x87, 0x47, 0x46, 0x86, 0x82, 0x42, 0x43, 0x83,
    0x41, 0x81, 0x80, 0x40
]

def calc_crc(data):
    ucCRCHi = 0xff
    ucCRCLo = 0xff

    for b in data:
        iIndex = ucCRCLo ^ b
        ucCRCLo = ucCRCHi ^ aucCRCHi[iIndex]
        ucCRCHi = aucCRCLo[iIndex]

    return bytes([ucCRCLo, ucCRCHi])

# Decode data - reading logic moved to main loop

@dataclass
class FramedPacket:
    seq: int
    typ: int
    data: int
    raw: bytes

class Framer:
    def __init__(self, channel):
        self.channel = channel
        self.acc = bytes()
        self.packets = []

    def add(self, data):
        self.acc = self.acc + data
        self.decode_all()

    def decode_all(self):
        while True:
            start_idx = self.acc.find(b"\x55\x00\x01")
            if start_idx == -1:
                break

            if start_idx != 0:
                self.on_drop(self.acc[:start_idx], "no_header")
                self.acc = self.acc[start_idx:]

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
                break

            dlen = self.acc[5] << 8 | self.acc[6]
            if len(self.acc) < 8 + dlen + 2:
                break

            data_crc = self.acc[8+dlen:8+dlen+2]
            calced_crc = calc_crc(self.acc[:8 + dlen])
            if data_crc != calced_crc:
                self.on_drop(self.acc[:3], "bad crc ({} != {})".format(data_crc, calced_crc))
                self.acc = self.acc[3:]
                break

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
            #print("ch{} packet {}".format(self.channel, packet))

    def on_drop(self, data, reason):
        print(self.channel, " dropped:", data, " ", reason)

sub_id_map = {
    0x101: "radar_hw_version",
    0x102: "radar_sw_version",
    0x103: "motion_detection",
    0x104: "presence_detection",
    0x105: "monitor_mode",
    0x106: "closing_setting",
    0x107: "edge_label",
    0x109: "import_export_label",
    0x110: "interference_source",
    0x111: "presence_detection_sensitivity",
    0x112: "location_report_enable",
    0x113: "reset_absent_status",
    0x114: "zone_detect_setting",
    0x115: "detect_zone_motion",
    0x116: "work_mode",
    0x117: "location_track_data",
    0x120: "angle_sensor_data",
    0x121: "fall_detection",
    0x122: "left_right_reverse",
    0x123: "fall_detection_sensitivity",
    0x125: "radar_interference_auto_setting",
    0x127: "ota_set_flag",
    0x128: "temperature",
    0x134: "fall_overtime_report_period",
    0x135: "fall_overtime_detection",
    0x138: "thermodynamic_chart_enable",
    0x139: "interference_auto_enable",
    0x141: "thermodynamic_chart_data",
    0x142: "detect_zone_presence",
    0x143: "device_direction",
    0x149: "edge_auto_setting",
    0x150: "edge_auto_enable",
    0x151: "detect_zone_sensitivity",
    0x152: "detect_zone_type",
    0x153: "radar_detect_zone_close_away_enable",
    0x154: "target_posture",
    0x155: "people_counting",
    0x156: "sleep_report_enable",
    0x157: "posture_report_enable",
    0x158: "people_counting_report_enable",
    0x159: "sleep_data",
    0x160: "delete_false_target",
    0x161: "sleep_state",
    0x162: "people_number_enable",
    0x163: "target_type_enable",
    0x164: "realtime_people_number",
    0x165: "ontime_people_number",
    0x166: "realtime_people_counting",
    0x167: "sleep_presence",
    0x168: "sleep_zone_mount_position",
    0x169: "sleep_zone_size",
    0x170: "wall_corner_mount_position",
    0x171: "sleep_inout_state",
    0x172: "dwell_time_enable",
    0x173: "walking_distance_enable",
    0x174: "walking_distance_all",
    0x176: "sleep_event",
    0x201: "debug_log",
    0x202: "aux_data",
}

def decode_sub_packet(channel, packet):
    sub_id = packet.data[0] << 8 | packet.data[1]
    sub_name = sub_id_map.get(sub_id)

    ## Type 1 packets are usually just the SubID (2 bytes total)
    #if packet.typ == 1 and len(packet.data) == 2:
    #    print(f"{channel}.{packet.typ}.{sub_id:04x} {sub_name} (ACK/Resp)")
    #    return

    attr_byte = packet.data[2] if len(packet.data) > 2 else None
    payload_data = packet.data[3:] if len(packet.data) > 3 else b""



    import struct

    # Decode generic value based on Type
    val_str = ""
    complex_output = []
    
    # Try to decode standard types
    decoded = False
    if attr_byte == 0x00: # UINT8
        if len(payload_data) >= 1:
            raw_val = payload_data[0]
            val_str = f"{raw_val} (0x{raw_val:02x})"
            decoded = True
    elif attr_byte == 0x01: # UINT16 
        if len(payload_data) >= 2:
            raw_val = struct.unpack(">H", payload_data[:2])[0]
            val_str = f"{raw_val} (0x{raw_val:04x})"
            decoded = True
    elif attr_byte == 0x02: # UINT32
        if len(payload_data) >= 4:
            raw_val = struct.unpack(">I", payload_data[:4])[0]
            val_str = f"{raw_val} (0x{raw_val:08x})"
            decoded = True
    elif attr_byte == 0x03: # VOID
        val_str = "VOID"
        decoded = True
    elif attr_byte == 0x04: # BOOL
        if len(payload_data) >= 1:
            raw_val = payload_data[0] != 0
            val_str = "TRUE" if raw_val else "FALSE"
            decoded = True
    elif attr_byte == 0x05: # BLOB1
        if len(payload_data) >= 2:
            blob_len = payload_data[0] << 8 | payload_data[1]
            val_str = f"STR[{blob_len}] {payload_data[2:].decode("ascii")}"
            decoded = True
    elif attr_byte == 0x06: # BLOB2
        if len(payload_data) >= 2:
            blob_len = payload_data[0] << 8 | payload_data[1]
            val_str = f"BLOB[{blob_len}]"
            decoded = True
            
    if not decoded:
         # Fallback for unknown types or malformed payloads
         val_str = f"RAW[{format_hex(packet.data[2:])}]"
    
    # Frame Type Icons
    # 1=Resp, 2=Write, 3=ACK, 4=Read, 5=Report
    type_icon = "?"
    if packet.typ == 1: type_icon = "<RSP"
    elif packet.typ == 2: type_icon = "WRT>"
    elif packet.typ == 3: type_icon = "<ACK"
    elif packet.typ == 4: type_icon = "REQ>"
    elif packet.typ == 5: type_icon = "<REP"

    dir_str = "ESP->Radar" if channel == 0 else "Radar->ESP"
    header_str = f"[{dir_str:<10}] {type_icon} {sub_name:<32} ({sub_id:04x}) Seq:{packet.seq:<3}"
    
    if packet.typ == 5 and sub_name == "location_track_data":
        sub_data_len = packet.data[3] << 8 | packet.data[4]
        sub_data = packet.data[5:5+sub_data_len]
        count = sub_data[0]
        complex_output.append(f"  Target Count: {count}")
        for n in range(count):
            item_data = sub_data[1+(14*n):1+(14*(n+1))]
            tid, x, y, z, speed, res, v6, v7, v8 = struct.unpack("<bhhhhHBBB", item_data)
            complex_output.append(f"    #{tid}: [{x}, {y}, {z}] Speed:{speed} Res:{res}")

    elif packet.typ == 5 and sub_name == "sleep_data":
        sub_data_len = packet.data[3] << 8 | packet.data[4]
        sub_data = packet.data[5:5+sub_data_len]
        count = sub_data[0]
        packet_size = 12
        complex_output.append(f"  Sleep Zones: {count}")
        num_items = (len(sub_data) - 1) // packet_size
        for n in range(num_items):
            item_data = sub_data[1+(packet_size*n):1+(packet_size*(n+1))]
            tid, zid, presence = struct.unpack("BBB", item_data[:3])
            unk = format_hex(item_data[3:])
            p_str = "Occupied" if presence else "Empty"
            complex_output.append(f"    #{tid} Zone {zid}: {p_str} | Raw: {unk}")
    
    # ACK status
    elif packet.typ == 2 and sub_name == "zone_detect_setting":
        if packet.data[2] == 0x06: # BLOB2
             blob_len = packet.data[3] << 8 | packet.data[4]
             blob_data = packet.data[5:]
             if len(blob_data) >= 41:
                 zone_id = blob_data[0]
                 cell_map_bytes = blob_data[1:41]
                 active_cells = []
                 for byte_idx, byte_val in enumerate(cell_map_bytes):
                     for bit_idx in range(8):
                         if (byte_val >> bit_idx) & 1:
                             active_cells.append(byte_idx * 8 + bit_idx)
                 
                 complex_output.append(f"  Zone ID: {zone_id} (0x{zone_id:02x})")
                 complex_output.append(f"  Active Cells ({len(active_cells)}): {active_cells}")
             else:
                 complex_output.append(f"  Raw Zone Data: {format_hex(packet.data)}")

    elif sub_name in ["edge_label", "import_export_label", "interference_source"]:
        if packet.data[2] == 0x06: # BLOB2
             blob_len = packet.data[3] << 8 | packet.data[4]
             blob_data = packet.data[5:]
             if len(blob_data) >= 40:
                 cell_map_bytes = blob_data[:40]
                 active_cells = []
                 for byte_idx, byte_val in enumerate(cell_map_bytes):
                     for bit_idx in range(8):
                         if (byte_val >> bit_idx) & 1:
                             active_cells.append(byte_idx * 8 + bit_idx)
                 complex_output.append(f"  Active Cells ({len(active_cells)}): {active_cells}")
             else:
                 complex_output.append(f"  Raw Map Data: {format_hex(blob_data)}")

    elif sub_name == "people_counting":
         if len(payload_data) >= 7:
             pc_id = payload_data[0]
             val_a = struct.unpack(">H", payload_data[1:3])[0]
             val_b = struct.unpack(">I", payload_data[3:7])[0]
             complex_output.append(f"  ID: {pc_id} | ValA: {val_a} | ValB: {val_b}")

    elif packet.typ == 3:
        status = (packet.data[2] << 8) | packet.data[3] if len(packet.data) >= 4 else 0
        status_str = "OK" if status == 0 else f"ERR({status})"
        val_str = f"{status_str}"

    print(f"{header_str} : {val_str}")
    for line in complex_output:
        print("  " + line)

framers = [Framer(0), Framer(1)]

files = [
    "test_decode/test_data.txt",
    "test_decode/test_data2.txt",
    "test_decode/test_data3.txt",
    "test_decode/test_data4.txt"
]

for filename in files:
    print(f"\n{'='*20} {filename} {'='*20}")
    data_rows = []
    try:
        with open(filename, "r") as f:
            for line in f:
                items = line.strip().split(" ")
                channel = int(items[0])
                dps = map(lambda a: int(a, 16), items[1:])
                dps_bytes = bytes(dps)
                data_rows.append((channel, dps_bytes))
    except FileNotFoundError:
        print(f"File not found: {filename}")
        continue

    # Reset framers for each file
    framers = [Framer(0), Framer(1)]
    for (channel, data) in data_rows:
        framers[channel].add(data)
        for packet in framers[channel].packets:
            decode_sub_packet(channel, packet)
        framers[channel].packets = []
