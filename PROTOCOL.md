### Confidence Annotation Key
*   **[CERTAIN]**: Verified by code logic or explicit constants. Default when not marked otherwise.
*   **[HIGH]**: Strong evidence from log patterns, but not explicitly enforced by code.
*   **[GUESS]**: Inferred from typical industry standards (e.g., mmWave radar conventions) or limited samples.
*   **[UNKNOWN]**: Insufficient data to determine.

---

## 1. Physical / Link Layer
*   **Transport**: UART
*   **Endianness**:
    *   Frame Fields (Length, SubID): **Big Endian**
    *   CRC: **Little Endian**
    *   Data Values (Coordinates): **Big Endian** **[HIGH]**

## 2. Frame Structure 
Total Length = $8 + N + 2$ bytes.

| Offset | Field | Type | Description |
| :--- | :--- | :--- | :--- |
| 0 | **Sync** | `u8` | Fixed `0x55` |
| 1 | **Ver_H** | `u8` | Fixed `0x00` (Protocol Version/ID) |
| 2 | **Ver_L** | `u8` | Fixed `0x01` (Protocol Version/ID) |
| 3 | **Seq** | `u8` | Sequence Number (Rolling 0-255) |
| 4 | **Type** | `u8` | Frame Type (See Sec 2.1) |
| 5 | **Len** | `u16` | Payload Length ($N$) |
| 7 | **HCheck**| `u8` | Header Checksum (See Sec 2.2) |
| 8 | **Payload**| `u8[N]`| Application Data |
| 8+N | **CRC** | `u16` | Frame CRC (See Sec 2.3) |

### 2.1 Frame Types
| Type | Direction | Name | Description |
| :--- | :--- | :--- | :--- |
| `0x01` | Host <- Dev | **Read Resp** | Response to Type `0x04` **[HIGH]** |
| `0x02` | Host -> Dev | **Write Req** | Set configuration |
| `0x03` | Both | **ACK** | Acknowledge Write (`0x02`) or Report (`0x05`) |
| `0x04` | Host -> Dev | **Read Req** | Request parameter value **[HIGH]** |
| `0x05` | Host <- Dev | **Report** | Asynchronous data (Push) |

### 2.2 Header Checksum
Sum bytes 0 through 6, subtract 1, invert, and mask.
$$ \text{HCheck} = \text{NOT} \left( \left( \sum_{i=0}^{6} \text{Byte}_i \right) - 1 \right) \pmod{256} $$

### 2.3 CRC-16
*   **Algorithm**: CRC-16 (Table-driven).
*   **Init**: `0xFFFF`
*   **Order**: Little Endian (Low Byte, High Byte).
*   **Coverage**: Bytes 0 through $(8+N-1)$.

---

## 3. Application Layer (Payloads)

All payloads begin with a 16-bit Sub-Command ID.

### 3.1 Generic ACK (Type 0x03)
Used to confirm receipt of Type `0x02` or `0x05`.

| Offset | Field | Type | Description |
| :--- | :--- | :--- | :--- |
| 0 | **SubID** | `u16` | The SubID being acknowledged |
| 2 | **Status**| `u16` | `0x0000` = Success **[HIGH]** |

### 3.2 Location Track Data (Report 0x05 / SubID 0x0117)
Describes tracked targets (coordinates, speed).

| Offset | Field | Type | Description |
| :--- | :--- | :--- | :--- |
| 0 | **SubID** | `u16` | Fixed `0x0117` |
| 2 | **Reserved**| `u8` | Fixed `0x06` in logs. Logic skips this. **[GUESS]** |
| 3 | **Len** | `u16` | Length of remaining data (`1 + 14 * K`) |
| 5 | **Count** | `u8` | Number of Targets (`K`) |
| 6 | **Target[]**| `struct` | List of `K` Target items (14 bytes each) |

**Target Item Structure (14 Bytes):**
*Note: Multi-byte integers are Big Endian.*

| Offset | Field | Type | Description |
| :--- | :--- | :--- | :--- |
| 0 | **ID** | `u8` | Target ID **[GUESS]** |
| 1 | **X** | `i16` | X Coordinate (mm) **[HIGH]** |
| 3 | **Y** | `i16` | Y Coordinate (mm) **[HIGH]** |
| 5 | **Vel_X** | `i16` | Velocity X (mm/s) **[GUESS]** |
| 7 | **Vel_Y** | `i16` | Velocity Y (mm/s) **[GUESS]** |
| 9 | **Mag** | `u16` | Magnitude / Resolution / Size **[UNKNOWN]** |
| 11 | **Type** | `u16` | Target Type? (Fixed `0x0002` in logs) **[UNKNOWN]** |
| 13 | **State** | `u8` | Target State (e.g., `0x00`=Static, `0x01`=Mov) **[GUESS]** |

### 3.3 Other Known Commands

#### 0x0102 - Radar SW Version (Report)
| Offset | Field | Type | Value / Note |
| :--- | :--- | :--- | :--- |
| 0 | **SubID** | `u16` | `0x0102` |
| 2 | **Major** | `u8` | e.g., `0x00` |
| 3 | **Minor** | `u8` | e.g., `0x56` (Version 0.86) |

#### 0x0128 - Temperature (Report)
| Offset | Field | Type | Value / Note |
| :--- | :--- | :--- | :--- |
| 0 | **SubID** | `u16` | `0x0128` |
| 2 | **Sign** | `u8` | `0x01` in logs (Positive?) **[GUESS]** |
| 3 | **Int** | `u8` | Integer part **[GUESS]** |
| 4 | **Frac** | `u8` | Fractional part or raw value **[UNKNOWN]** |

#### 0x0112 - Location Report Enable (Write)
| Offset | Field | Type | Value / Note |
| :--- | :--- | :--- | :--- |
| 0 | **SubID** | `u16` | `0x0112` |
| 2 | **Enable** | `u8` | `0x04`? (Log shows `01 12 04 01`) **[UNKNOWN]** |
| 3 | **State** | `u8` | `0x01` = On **[HIGH]** |

#### 0x0143 - Device Direction (Read Req / Resp)
**Request:** `01 43 00 02` (Payload `00 02` is likely "Read Length" or "Param ID") **[GUESS]**
**Response:**
| Offset | Field | Type | Value / Note |
| :--- | :--- | :--- | :--- |
| 0 | **SubID** | `u16` | `0x0143` |
| 2 | **Dir** | `u8` | Mounting Direction |
| 3 | **Pos** | `u8` | Mounting Position (e.g., `0x02`=Top) |


### 3.4 Complete Command Reference

#### Core Device Commands (0x0101-0x0109)
0x0101: radar_hw_version
0x0102: radar_sw_version
0x0103: motion_detection
0x0104: presence_detection
0x0105: monitor_mode
0x0106: closing_setting
0x0107: edge_label
0x0109: import_export_label

#### Detection & Zone Configuration (0x0110-0x0127)
0x0110: interference_source
0x0111: presence_detection_sensitivity
0x0112: location_report_enable
0x0113: reset_absent_status
0x0114: zone_detect_setting
0x0115: detect_zone_motion
0x0116: work_mode
0x0117: location_track_data
0x0120: angle_sensor_data
0x0121: fall_detection
0x0122: left_right_reverse
0x0123: fall_detection_sensitivity
0x0125: radar_interference_auto_setting
0x0127: ota_set_flag

#### Sensors & Environmental Data (0x0128-0x0143)
0x0128: temperature
0x0134: fall_overtime_report_period
0x0135: fall_overtime_detection
0x0138: thermodynamic_chart_enable
0x0139: interference_auto_enable
0x0141: thermodynamic_chart_data
0x0142: detect_zone_presence
0x0143: device_direction

#### Advanced Zone & Sleep Detection (0x0149-0x0176)
0x0149: edge_auto_setting
0x0150: edge_auto_enable
0x0151: detect_zone_sensitivity
0x0152: detect_zone_type
0x0153: radar_detect_zone_close_away_enable
0x0154: target_posture
0x0155: people_counting
0x0156: sleep_report_enable
0x0157: posture_report_enable
0x0158: people_counting_report_enable
0x0159: sleep_data
0x0160: delete_false_target
0x0161: sleep_state
0x0162: people_number_enable
0x0163: target_type_enable
0x0164: realtime_people_number
0x0165: ontime_people_number
0x0166: realtime_people_counting
0x0167: sleep_presence
0x0168: sleep_zone_mount_position
0x0169: sleep_zone_size
0x0170: wall_corner_mount_position
0x0171: sleep_inout_state
0x0172: dwell_time_enable
0x0173: walking_distance_enable
0x0174: walking_distance_all
0x0176: sleep_event

#### Debug & Utility (0x0201-0x0202)
0x0201: debug_log
0x0202: aux_data
