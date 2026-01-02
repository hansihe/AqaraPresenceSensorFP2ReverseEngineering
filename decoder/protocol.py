import struct

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

def format_hex(data):
    return " ".join("{:02x}".format(c) for c in data)

def decode_packet(channel, packet, exclude_names=None):
    output_lines = []
    
    sub_id = packet.data[0] << 8 | packet.data[1]
    sub_name = sub_id_map.get(sub_id)
    if sub_name is None:
        sub_name = "UNKNOWN"

    if exclude_names and sub_name in exclude_names:
        return []

    attr_byte = packet.data[2] if len(packet.data) > 2 else None
    payload_data = packet.data[3:] if len(packet.data) > 3 else b""

    # Decode generic value based on Type
    val_str = ""
    complex_output = []
    
    # Try to decode standard types
    decoded = False
    if packet.typ == 1 and len(packet.data) == 2:
        val_str = "Device Value Request"
        decoded = True
    if attr_byte == 0x00: # UINT8
        if len(payload_data) >= 1:
            raw_val = payload_data[0]
            val_str = f"UINT8: {raw_val} (0x{raw_val:02x})"
            decoded = True
    elif attr_byte == 0x01: # UINT16
        if len(payload_data) >= 2:
            raw_val = struct.unpack(">H", payload_data[:2])[0]
            val_str = f"UINT16: {raw_val} (0x{raw_val:04x})"
            decoded = True
    elif attr_byte == 0x02: # UINT32
        if len(payload_data) >= 4:
            raw_val = struct.unpack(">I", payload_data[:4])[0]
            val_str = f"UINT32: {raw_val} (0x{raw_val:08x})"
            decoded = True
    elif attr_byte == 0x03: # VOID
        val_str = "VOID"
        decoded = True
    elif attr_byte == 0x04: # BOOL
        if len(payload_data) >= 1:
            raw_val = payload_data[0] != 0
            val_str = f"BOOL: {'TRUE' if raw_val else 'FALSE'}"
            decoded = True
    elif attr_byte == 0x05: # BLOB1
        if len(payload_data) >= 2:
            blob_len = payload_data[0] << 8 | payload_data[1]
            try:
                val_str = f"STR[{blob_len}]: {payload_data[2:].decode('ascii')}"
            except:
                 val_str = f"STR[{blob_len}]: (Binary) {format_hex(payload_data[2:])}"
            decoded = True
    elif attr_byte == 0x06: # BLOB2
        if len(payload_data) >= 2:
            blob_len = payload_data[0] << 8 | payload_data[1]
            val_str = f"BLOB[{blob_len}]: {format_hex(payload_data[2:])}"
            decoded = True
            
    if not decoded:
         # Fallback for unknown types or malformed payloads
         if len(packet.data) > 2:
            val_str = f"RAW[{format_hex(packet.data[2:])}]"
         else:
            val_str = "TRUNCATED"
    
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
    
    # Custom decoders for specific messages
    if packet.typ == 5 and sub_name == "location_track_data":
        sub_data_len = packet.data[3] << 8 | packet.data[4]
        sub_data = packet.data[5:5+sub_data_len]
        if len(sub_data) > 0:
            count = sub_data[0]
            complex_output.append(f"  Target Count: {count}")
            for n in range(count):
                item_data = sub_data[1+(14*n):1+(14*(n+1))]
                if len(item_data) == 14:
                    tid, x, y, z, velocity, snr, classifier, posture, active = struct.unpack(">BhhhhHBBB", item_data)
                    complex_output.append(f"    #{tid}: [{x}, {y}, {z}] Velocity:{velocity} SNR:{snr} Class:{classifier} Posture:{posture} Active:{active}")

    elif sub_name in ["detect_zone_motion", "detect_zone_presence"]:
        # Structure seems to be [ZoneID] [State]
        # Data is UINT16, so Payload[0] is ZoneID, Payload[1] is State
        if len(payload_data) >= 2:
           # For UINT16 decoding, the raw bytes were already consumed or are in packet.data
           # But here 'payload_data' is a slice. 
           # Wait, earlier code for UINT16 does: struct.unpack(">H", payload_data[:2])
           # So payload_data[0] is MSB (ZoneID), payload_data[1] is LSB (State)
           
           zone_id = payload_data[0]
           state = payload_data[1]
           
           # Decode Motion States (0x0115) - based on observation
           # 0x01=Enter? 0x02=Move? 0x04=Exit? 0x08=Left/Right? 0x10=Interference?
           # Just print hex state for now with generic label
           
           event_type = "Motion" if sub_name == "detect_zone_motion" else "Presence"
           val_str = f"Zone:{zone_id} State:{state} (0x{state:02x})"
           
           if sub_name == "detect_zone_presence":
               val_str += " [Occupied]" if state == 1 else " [Empty]"

           # Override standard decoded string
           decoded = True

    elif sub_name in ["zone_detect_setting", "interference_source", "import_export_label", "edge_label"]:
        # Handle Map payloads
        # payload_data includes 2 bytes of Length at the start (BLOB header)
        # So actual data starts at index 2.
        
        map_data = b""
        zone_id = None
        
        # zone_detect_setting: [LenH] [LenL] [ZoneID] [Map 40B]
        # Total Len = 43 (2 + 1 + 40)
        if sub_name == "zone_detect_setting" and len(payload_data) >= 43:
            zone_id = payload_data[2]
            map_data = payload_data[3:43]
            complex_output.append(f"  Zone ID: {zone_id}")
            
        # Other maps: [LenH] [LenL] [Map 40B]
        # Total Len = 42 (2 + 40)
        elif len(payload_data) >= 42:
            map_data = payload_data[2:42]
            
        if len(map_data) == 40:
            complex_output.append("  Map (20x16):")
            # 20 rows, 2 bytes (16 bits) per row
            for row in range(20):
                row_bytes = map_data[row*2:(row+1)*2]
                row_val = (row_bytes[0] << 8) | row_bytes[1]
                row_str = ""
                for col in range(16):
                    # Check bit (15-col) for Big Endian mapping
                    if (row_val >> (15-col)) & 1:
                        row_str += "##"
                    else:
                        row_str += ".."
                complex_output.append(f"    {row:02d}: {row_str}")

    # Enum Maps
    zone_sensitivity_map = {1: "Low", 2: "Medium", 3: "High"}
    zone_type_map = {
        2: "Television Area",
        10: "Others/GreenPlant", 
        11: "Leisure Area",
        13: "Dressing Table",
        14: "Closet", 
        15: "Desk",
        23: "Shower",
        36: "Stairs"
    }
    lr_reverse_map = {0: "Consistent", 1: "Opposite"}
    wall_pos_map = {1: "Wall"}

    if packet.typ != 3:
        if sub_name == "detect_zone_sensitivity":
            # Val is [ZoneID] [Sens]
            if 'raw_val' in locals() and isinstance(raw_val, int): 
                zid = (raw_val >> 8) & 0xFF
                sens = raw_val & 0xFF
                sens_str = zone_sensitivity_map.get(sens, str(sens))
                val_str = f"{raw_val} (0x{raw_val:04x}) [Zone:{zid} Sens:{sens_str}]"

        elif sub_name == "detect_zone_type":
            # Val is [ZoneID] [Type]
            if 'raw_val' in locals() and isinstance(raw_val, int):
                zid = (raw_val >> 8) & 0xFF
                ztype = raw_val & 0xFF
                type_str = zone_type_map.get(ztype, str(ztype))
                val_str = f"{raw_val} (0x{raw_val:04x}) [Zone:{zid} Type:{type_str}]"
                
        elif sub_name == "radar_detect_zone_close_away_enable":
            # Val is [ZoneID] [Bool]
            if 'raw_val' in locals() and isinstance(raw_val, int):
                zid = (raw_val >> 8) & 0xFF
                enable = raw_val & 0xFF
                en_str = "ON" if enable == 1 else "OFF"
                val_str = f"{raw_val} (0x{raw_val:04x}) [Zone:{zid} CloseAway:{en_str}]"

        elif sub_name == "left_right_reverse":
            if 'raw_val' in locals() and isinstance(raw_val, int):
                val_str += f" [{lr_reverse_map.get(raw_val, 'Unknown')}]"
                
        elif sub_name == "wall_corner_mount_position":
             if 'raw_val' in locals() and isinstance(raw_val, int):
                val_str += f" [{wall_pos_map.get(raw_val, 'Unknown')}]"

    if packet.typ == 3:
        status = (packet.data[2] << 8) | packet.data[3] if len(packet.data) >= 4 else 0
        status_str = "OK" if status == 0 else f"ERR({status})"
        val_str = f"{status_str}"

    output_lines.append(f"{header_str} : {val_str}")
    for line in complex_output:
        output_lines.append("  " + line)
        
    return output_lines
