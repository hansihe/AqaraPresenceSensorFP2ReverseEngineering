### Confidence Annotation Key
*   **[CERTAIN]**: Verified by code logic or explicit constants. Default when not marked otherwise.
*   **[VERIFIED]**: Confirmed by decoding real data dumps with `test_decode` script.
*   **[GUESS]**: Inferred from typical industry standards (e.g., mmWave radar conventions) or limited samples.
*   **[UNKNOWN]**: Insufficient data to determine.

---

---
## 1. Physical Layer
*   **Interface**: UART (Universal Asynchronous Receiver-Transmitter)
*   **Baud Rate**: *Unknown* (Likely 115200 or higher based on payload volume)
*   **Connection**:
    *   **Channel 0 (ESP -> Radar)**: Commands (Type 2/4) and ACKs (Type 3). Master/Host role.
    *   **Channel 1 (Radar -> ESP)**: Responses (Type 1), ACKs (Type 3), and asynchronous Reports (Type 5). Slave/Module role.
    
---

## 2. High-Level Operation

### 2.1 roles
*   **Host (ESP32)**: Acts as the **Master**. It initiates configuration, controls state, and acknowledges reports.
*   **Module (Radar)**: Acts as the **Slave**. It responds to requests and asynchronously "Reports" data (Push model) once enabled.

### 2.2 Heartbeat
The Radar module sends a `radar_sw_version` (`0x0102`) Report approximately every 1 second as a heartbeat.
*   **Payload**: `VOID` (Length 0).
*   **Purpose**: Indicates the radar is alive and powered.
*   **Behavior**: The Host (ESP) does not usually ACK this specific report in the logs, possibly because it's a broadcast/heartbeat (though ACKs are seen for other reports). *Correction: ACKs ARE seen for sw_version in some traces, but not always required for link maintenance?*

### 2.3 Startup Sequence
Based on captured boot logs, the initialization handshake follows this pattern:

1.  **Announcement**: Radar sends `radar_sw_version` (Heartbeat) to indicates it's ready.
2.  **Basic Inquiry**: Host requests static info:
    *   `temperature` (`0x0128`)
    *   `device_direction` (`0x0143`)
    *   `angle_sensor_data` (`0x0120`)
3.  **Configuration**: Host writes settings (often in a burst):
    *   `monitor_mode` (`0x0105`)
    *   `installation_settings` (Reverse, Heights, etc.)
    *   `sensitivities` (Presence, Fall, Zone)
    *   `work_mode` (`0x0116`)
4.  **Enable Reporting**: Crucially, the Host sends commands to enable data streams:
    *   **`location_report_enable` (`0x0112`)** -> Set to `TRUE` to start the stream of `0x0117` BLOBs.
5.  **Steady State**:
    *   ESP sends `ACK` for received data.
    *   Radar streams `location_track_data` (`0x0117`) approx 10-20Hz (fast).
    *   Radar sends `radar_sw_version` (`0x0102`) approx 1Hz.

---

## 3. Architecture: The Attribute System

The device protocol is fundamentally an **Attribute Access Protocol**. Almost every operation involves reading, writing, or reporting a specific "Attribute" identified by a 16-bit `SubID`.

The firmware contains a central `radar_attribute_table` which maps every `SubID` to:
1.  **Handler Function**: Code to execute when this attribute is accessed.
2.  **Expected Data Type**: The type of data associated with this attribute.
3.  **Permissions**: Which operations (Read/Write/Report) are valid (enforced by `validateSubCommandWithOperation`).

### 2.1 Operation Types (Frame Types)
The "Command" byte in the UART frame actually defines the *operation* being performed on the Attribute.

| Type | Direction | Name | Meaning |
| :--- | :--- | :--- | :--- |
| `0x01` | Host <- Dev | **Read Response** | Device returning a requested attribute value. |
| `0x02` | Host -> Dev | **Write Request** | Host setting an attribute value. |
| `0x03` | Both | **ACK** | Confirmation of a Write or Report. |
| `0x04` | Host -> Dev | **Read Request** | Host asking for an attribute value. |
| `0x05` | Host <- Dev | **Report** | Device spontaneously sending an attribute value (Push). |

## 4. Low-Level Transport

*   **Transport**: UART
*   **Endianness**: Mixed.
    *   **Frame Header**: Big Endian (unconfirmed, but standard for this protocol family)
    *   **Payload Header**: Little Endian (SubID is LE in some contexts, BE in others - *Correction: Code analysis shows `cmd_id` calculated as `buf[1] + buf[0]*256`, which is **Big Endian**.*)
    *   **Data Values**: Big Endian (e.g., `val = buf[3]*256 + buf[4]`)
    *   **CRC**: Little Endian

### 3.1 Frame Structure 
Total Length = $8 + N + 2$ bytes.

| Offset | Field | Type | Description |
| :--- | :--- | :--- | :--- |
| 0 | **Sync** | `u8` | Fixed `0x55` |
| 1 | **Ver_H** | `u8` | Fixed `0x00` |
| 2 | **Ver_L** | `u8` | Fixed `0x01` |
| 3 | **Seq** | `u8` | Sequence Number |
| 4 | **OpCode** | `u8` | Operation Type (1-5, see Sec 1.1) |
| 5 | **Len** | `u16` | Payload Length ($N$) |
| 7 | **HCheck**| `u8` | Header Checksum |
| 8 | **Payload**| `u8[N]`| Attribute Payload (See Sec 3) |
| 8+N | **CRC** | `u16` | CRC-16 (Little Endian) |

### 3.2 Header Checksum
$$ \text{HCheck} = \text{NOT} \left( \left( \sum_{i=0}^{6} \text{Byte}_i \right) - 1 \right) \pmod{256} $$

### 3.3 CRC-16
*   **Algorithm**: CRC-16/MODBUS (Poly `0x8005`, Init `0xFFFF`)
*   **Coverage**: Bytes 0 through $(8+N-1)$

---

## 5. Attribute Payload Structure

The payload for **ALL** operation types follows a strict structure parsed by `radar_package_deserialize`.

| Offset | Field | Type | Description |
| :--- | :--- | :--- | :--- |
| 0 | **SubID** | `u16` | Attribute ID (Big Endian) |
| 2 | **DataType**| `u8` | Type of following data (See Sec 4.1) |
| 3 | **Data** | `var` | Value (Format depends on DataType) |

### 4.1 Data Types
The `DataType` byte determines how the rest of the payload is parsed.

| Type ID | Name | Size | Encoding |
| :--- | :--- | :--- | :--- | :--- |
| `0x00` | **UINT8** | 1 | Single byte: `buf[3]` |
| `0x01` | **UINT16** | 2 | Big Endian: `buf[3]<<8 | buf[4]` |
| `0x02` | **UINT32** | 4 | Big Endian |
| `0x03` | **VOID** | 0 | No data follows. Used for simple triggers/ACKs. |
| `0x04` | **BOOL** | 1 | `buf[3] != 0` |
| `0x05` | **STRING (BLOB1)** | $2+N$ | Length (`u16` BE) followed by $N$ bytes of ASCII string. |
| `0x06` | **BLOB2 (Binary)** | $2+N$ | Length (`u16` BE) followed by $N$ bytes of binary data. |

---


### 4.2 Complex Payloads

#### 4.2.3 Zone Detection Settings (0x0114) **[CERTAIN]**
This attribute defines the layout of a detection zone. The payload is 41 bytes.
*   **Zone ID**: `u8` (Byte 0). Identifies the zone being configured (e.g., `0x01` = Zone 1).
*   **Cell Map**: `u8[40]` (Bytes 1-40). A 320-bit bitmask representing the 320-cell detection grid.
    *   Each bit corresponds to a cell in the grid.
    *   `1` = Cell is part of this zone.
    *   `0` = Cell is not part of this zone.
    *   *Note: In the cloud/app protocol, this payload is preceded by an 'Operation' byte (1=Add/Update?), making the cloud command 42 bytes.*

#### 4.2.4 Location Track Data (0x0117) **[VERIFIED]**
The payload consists of a list of targets. The data is preceded by the standard BLOB header (which contains the total length).
Inside the BLOB:
*   **Target Count**: `u8` (inferred from loop count)
*   **Target List**: Array of 14-byte structures.

| Offset | Field | Type | Description |
| :--- | :--- | :--- | :--- |
| 0 | `TargetID` | `u8` | Unique ID of the tracked target |
| 1 | `X` | `s16` | X Coordinate (Little Endian in payload, swapped for log?) |
| 3 | `Y` | `s16` | Y Coordinate |
| 5 | `Z` | `s16` | Z Coordinate |
| 7 | `Speed` | `s16` | Speed/Velocity |
| 9 | `Resolution`| `u16` | Resolution/Distance confidence? |
| 11 | `Val6` | `u8` | Unknown |
| 12 | `Val7` | `u8` | Unknown |
| 13 | `Val8` | `u8` | Unknown |

*Note: The coordinate endianness in the raw stream appears to be Little Endian, as the logging code manually swaps bytes `(uVar5 >> 8) | (uVar5 << 8)` to display them.*

#### 4.2.2 Sleep Data (0x0159) **[VERIFIED]**
The payload contains sleep tracking information per zone.
*   **Item Count**: `u8` (Usually 1)
*   **Items**: Array of 12-byte structures.

| Offset | Field | Type | Description |
| :--- | :--- | :--- | :--- |
| 0 | `TargetID` | `u8` | Tracked Target ID |
| 1 | `ZoneID` | `u8` | Zone ID |
| 2 | `Presence` | `u8` | Presence/Occupancy state? |
| 3-11 | `Unknown`| `u8[9]` | Vital signs or Sleep Stage data (Heart rate, Breath rate, etc.) |

---

## 6. Attribute Reference

The following table is derived from the firmware's `radar_attribute_table` and `subCommandWithOperationValidityTable`.
*   **RW**: Read/Write permissions (derived from Validity Table). `R`=Read(4)/Resp(1), `W`=Write(2), `Rep`=Report(5).
*   **Type**: Data Type expected.

### 6.1 System & Versioning
| SubID | Name | Type | RW | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0x0101` | `hw_version` | `UINT8` | R | Hardware Version |
| `0x0102` | `sw_version` | `UINT8` | R | Software Version |
| `0x0103` | `motion_det` | `UINT8` | RW | Motion Detection Enable (1=On, 0=Off) |
| `0x0104` | `presence_det` | `UINT8` | RW | Presence Detection Enable (1=On, 0=Off) |
| `0x0128` | `temperature` | `UINT16` | R | Chip Temperature |
| `0x0201` | `debug_log` | `BLOB1` | Rep| Debug Log Data |

### 6.2 Mode Configuration
| SubID | Name | Type | RW | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0x0105` | `monitor_mode` | `UINT8` | RW | Monitoring Mode (Raw Int, verify in App) |
| `0x0106` | `closing_setting`| `UINT8` | RW | Closing Setting (Raw Int) |
| `0x0116` | `work_mode` | `UINT8` | RW | Work Mode (Raw Int) |
| `0x0122` | `lr_reverse` | `UINT8` | RW | Left/Right Reverse (Installation) |
| `0x0127` | `ota_set_flag` | `?` | W | OTA Update Flag |
| `0x0143` | `device_direction`| `?` | R | Device Direction (Installation) |

### 6.3 Detection Zones & Configuration
| SubID | Name | Type | RW | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0x0107` | `edge_label` | `BLOB2` | RW | Edge Label (40-byte Grid Map) |
| `0x0109` | `imp_exp_label` | `BLOB2` | RW | Import/Export Label (40-byte Map) |
| `0x0110` | `interfer_src` | `BLOB2` | RW | Interference Source (40-byte Map) |
| `0x0114` | `zone_det_set` | `BLOB2` | RW | Zone Set (1B ZoneID + 40B Map) |
| `0x0150` | `edge_auto_en` | `BOOL` | RW | Edge Auto Enable |
| `0x0151` | `zone_sens` | `UINT16` | RW | Zone Sensitivity Array |
| `0x0152` | `detect_zone_type`| `UINT16` | RW | Reference Zone Type Array |
| `0x0153` | `zone_cls_away`| `UINT16` | RW | Close/Away Zone Enable |
| `0x0160` | `del_false_tgt` | `UINT8` | W | Delete False Target |
| `0x0163` | `tgt_type_en` | `BOOL` | RW | Target Type Detection Enable |
| `0x0149` | `edge_auto_set` | `BLOB2` | RW | Edge Auto Setting |
| `0x0125` | `inter_auto_set` | `BLOB2` | RW | Interference Auto Setting |

### 6.4 Reporting & Tracking
| SubID | Name | Type | RW | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0x0112` | `loc_rep_en` | `BOOL` | RW | Location Report Enable |
| `0x0117` | `loc_track_data`| `BLOB2` | Rep| **Location Tracking Data** (See 4.2.1) |
| `0x0155` | `people_counting`| `BLOB2` | Rep| People Counting (7B: ID, ValA, ValB) |
| `0x0157` | `posture_rep_en`| `BOOL` | RW | Posture Report Enable |
| `0x0158` | `ppl_cnt_rep_en`| `BOOL` | RW | People Counting Report Enable |
| `0x0162` | `ppl_num_en` | `BOOL` | RW | People Number Enable |
| `0x0164` | `realtime_ppl` | `UINT32` | Rep| Realtime People Number |
| `0x0165` | `ontime_ppl` | `UINT32` | Rep| Ontime People Number |
| `0x0166` | `realtime_cnt` | `UINT32` | Rep| Realtime People Counting |
| `0x0175` | `zone_ppl_num` | `UINT16` | Rep| Zone People Number (`0xZZNN`) |

### 6.5 Sleep & Wellness
| SubID | Name | Type | RW | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0x0156` | `sleep_rep_en` | `BOOL` | RW | Sleep Report Enable |
| `0x0159` | `sleep_data` | `BLOB2` | Rep| Sleep Data (See 4.2.2) |
| `0x0161` | `sleep_state` | `UINT8` | Rep| Sleep State (Enum: InBed/Out/Awake?) |
| `0x0168` | `sleep_mt_pos` | `UINT8` | RW | Sleep Zone Mount Position |
| `0x0169` | `sleep_zn_size` | `UINT32` | RW | Sleep Zone Size (Hi16=W, Lo16=L) |
| `0x0171` | `sleep_inout` | `UINT8` | Rep| Sleep In/Out State |
| `0x0176` | `sleep_event` | `UINT8` | Rep| Sleep Event Trigger |
| `0x0167` | `sleep_presence`| `UINT8` | Rep| Sleep Presence |
| `0x0154` | `target_posture`| `UINT16` | Rep| Target Posture Data |

### 6.6 Advanced Settings
| SubID | Name | Type | RW | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0x0121` | `fall_det` | `UINT8` | RW | Fall Detection Enable |
| `0x0123` | `fall_sens` | `UINT8` | RW | Fall Detection Sensitivity |
| `0x0134` | `fall_ot_per` | `UINT32` | RW | Fall Overtime Report Period |
| `0x0135` | `fall_ot_det` | `UINT32` | RW | Fall Overtime Detection |
| `0x0138` | `thermo_en` | `BOOL` | RW | Thermodynamic Chart Enable |
| `0x0139` | `inter_auto_en` | `BOOL` | RW | Interference Source Auto Enable |
| `0x0141` | `thermo_data` | `BLOB2` | Rep| Thermodynamic Chart Data |
| `0x0142` | `zone_presence` | `UINT16` | Rep| Zone Presence Map (Bitmask?) |
| `0x0170` | `wall_corn_pos` | `UINT8` | RW | Wall Corner Mount Position |
| `0x0172` | `dwell_time_en` | `BOOL` | RW | Dwell Time Enable |
| `0x0173` | `walk_dist_en` | `BOOL` | RW | Walking Distance Enable |
| `0x0174` | `walk_dist_all` | `UINT32` | Rep| Walking Dist Total |

## 7. Reverse Engineering Focus

To achieve full control, the following areas require further reverse engineering:

1.  **Enum Value Mapping**:
    *   Locate the string-to-integer mapping logic for `monitor_mode`, `work_mode`, and `sleep_state`.
    *   *Lead*: Search for functions like `radar_rxsub_alt_cloud_monitor_mode`. These handlers likely parse the string text from the cloud (e.g., "left_mounting") and convert it to the `UINT8` sent to UART.
    *   *Lead*: Check `FUN_400df370` and surrounding data areas for string tables.

2.  **BLOB Structure Parsing**:
    *   `edge_label` (0x0107) and `zone_type` (0x0152): These config payloads control critical features. Analyze `radar_rxsub_alt_cloud_edge_label` or similar to see how they pack data from the cloud format into the BLOB.

3.  **Sleep Data Payload**:
    *   Analyze `radar_rxsub_radar_sleep_data` to understand the 12-byte structure.



## 8. Reverse Engineering Notes
*   **Dispatch Logic**: The main handler checks `g_cmd_permission_table` to verify if the received Frame Type (Read/Write/etc.) is allowed for the specific SubID.
*   **Control Flow Pattern**: The firmware maintains two sets of handlers for many attributes:
    *   `radar_rxsub_radar_X`: Handles **incoming UART** packets (Reports/ACKs). Updates global state, then pushes to Cloud/App.
    *   `radar_rxsub_alt_cloud_X`: Handles **incoming Cloud/App** commands. Writes to UART to configure Radar.
*   **Special Data Handling**:
    *   `sleep_zone_size` (`0x0169`): The `UINT32` value is split. High 16 bits = `bedWidth`, Low 16 bits = `bedLength`.
    *   `zone_people_number` (ID Unknown, inferred): Value `0xZZNN` -> `ZZ`=ZoneID, `NN`=Count.

