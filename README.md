# edLoRa Protocol
[![PyPI version](https://img.shields.io/pypi/v/edlora.svg?color=blue)](https://pypi.org/project/edlora/)

*edLoRa* is an ultra-lightweight, high-performance binary telemetry protocol engineered specifically for high-power rocketry, high-altitude balloons, and long-range UAVs utilizing LoRa transceivers. 

It completely abandons bandwidth-heavy JSON or text strings in favor of static **struct-packed binary payloads**, ensuring strict data density limits while delivering mathematical packet loss tracking, cross-language interoperability (C++ on the vehicle, Python on the Ground Station), and cryptographic obfuscation.

### 🌟 Why edLoRa over JSON?
When utilizing LoRa at high spread factors (SF10-12) for extreme range operations, duty-cycle regulations limit your transmission rate to mere bytes-per-second. An 80-byte JSON string like `{"alt": 1500, "vel": 20}` takes massive airtime. In `edLoRa`, this same exact telemetry encapsulates into a heavily-protected mathematical binary struct taking less than a fraction of the time to transmit.

## 🚀 Key Features
- **Strict Binary Packing:** 100% string-free packing. Minimizes 'Time-on-Air' (ToA) to adhere to strict 1% RF duty cycle limits.
- **Robust Hardware Framing:** A fixed `0xED` Sync Byte, sequential Payload Length checking, and CCITT CRC-16 checksums mathematically guarantee that your ground station never parses garbage UART data from an overloaded receiver.
- **Versioned Protocol (v2.0):** Features a fixed `12-byte` routing header encompassing strict `version` validation, meaning future protocol iterations won't crash your ground station parsers.
- **Dynamic Bitmask Flags:** Built-in protocol-level flags handle properties like `ACK_REQUIRED`, `ENCRYPTED`, or `FRAGMENTED` without wasting precious `MsgType` designations.
- **Multi-Node Routing:** Integrated `Sender ID` and `Receiver ID` bytes natively support Swarm topologies or Ground-to-Rocket targeting (`0xFF` acts as a Broadcast blanket).
- **Embedded Zero-Heap C++:** The C++ serializer/deserializer completely avoids dynamic memory allocations, permanently protecting ESP32, STM32, and Arduino microcontrollers against heap fragmentation over multi-hour flight profiles.

## 📦 What's New in v2.0?
The v2.0 upgrade completely rebuilt the protocol header to establish a massive leap in long-term stability and routing potential:
1. **The `Version` Byte (`0x02`):** Parsers now actively reject packets from mismatched hardware revisions.
2. **The `Flags` Byte:** Added an 8-bit flag matrix to the header. We can now mark a packet as an `ACK` or `ENCRYPTED` using a single bit, rather than inventing endless unique `MsgType`s for variants of the same telemetry.
3. **12-byte Super Header:** The new `[Sync | Version | Flags | Sender | Receiver | MsgType | SeqNum | Timestamp | Length]` format uniquely packs 12 bytes of immensely powerful metadata onto the front of every transmission, leaving up to 240 bytes entirely free for your payload structures.

## Extensive Documentation
If you are planning to deploy `edLoRa` for a competition-grade architecture, please review the extensive documentation to fully understand the protocol specification and how to utilize it effectively:
- 📖 [Protocol Architecture & Reasoning](https://github.com/BenEgeDeniz/edLoRa/blob/main/docs/architecture.md) — *Why the protocol relies on binary struct-packing, Sync Bytes, auto-injected timestamps, and how the `MsgType::ACK` (Command Acknowledgement) bouncing mathematically maps packet delivery.*
- 🚀 [Getting Started Guide](https://github.com/BenEgeDeniz/edLoRa/blob/main/docs/getting_started.md) — *In-depth code implementation details for initializing, packing, and securely parsing valid buffers on both ESP32/Arduino and Python.*
- 💻 [CLI Stream Monitor](https://github.com/BenEgeDeniz/edLoRa/blob/main/docs/cli_monitor.md) — *How to test your packet layout by streaming raw RF bytes directly from a serial LoRa module into a terminal window using the `examples/cli_monitor.py` GUI.*

## Directory Structure
- `cpp/`: C++ header (`edlora.h`) and source implementation for ESP32/Linux.
- `python/`: Python 3.x module (`edlora.py`) for the Ground Station / decoding logic.
- `examples/`: Sample usage scripts demonstrating perfect cross-language compatibility.
  - `test_linux.cpp` and `test_python.py` demonstrate basic raw packing/unpacking.
## Message Types (`MsgType`)
To allow for structured data, `edLoRa` categorizes packets using the `MsgType` byte:

| Name | Hex Value | Description |
| ---- | --------- | ----------- |
| `HEARTBEAT` | `0x00` | Simple keep-alive or ping. |
| `GPS` | `0x01` | Latitude, Longitude, Fix Type, Sat count. |
| `ALTIMETER` | `0x02` | Altitude and barometric pressure data. |
| `IMU` | `0x03` | Raw Accel, Gyro, Mag data. |
| `COMMAND` | `0x04` | Ground-to-vehicle commands or text logs. |
| `SYS_STATE` | `0x05` | System battery, temp, and current flight phase. |
| `ORIENTATION` | `0x06` | Calculated attitude (Quaternions/Euler angles). |
| `EVENT` | `0x07` | Major flight events (Liftoff, MECO, Apogee, Deployment). |
| `VELOCITY` | `0x08` | Vertical velocity data. |
| `ACK` | `0xFD` | Command Acknowledgement (Payload = original `seq_num`). |
| `ERROR_MSG` | `0xFE` | Faults and system error states. |
| `CUSTOM` | `0xFF` | Freeform binary payloads. |

### Recommended Payload Schemas
For standard interoperability between the C++ flight systems and Python ground stations, `edLoRa` expects the following exact byte-packing schemas (Standard **Little-Endian** formatting) for specific `MsgType`s. 

| MsgType | C++ Struct / Variables | Python `struct` format | Total Size | Description |
| ------- | ---------------------- | ---------------------- | ---------- | ----------- |
| `ALTIMETER` | `int32_t alt_cm`<br>`uint32_t press_pa` | `<iI` | 8 bytes | Altitude in cm, Barometric pressure in Pa. |
| `VELOCITY` | `int16_t vz_ms10` | `<h` | 2 bytes | Vertical velocity in m/s multiplied by 10. |
| `ACK` | `uint8_t seq_num` | `<B` | 1 byte | Contains the `seq_num` of the command being acknowledged. |
| `COMMAND` | `char str[]` | UTF-8 String | Variable | Plain-text ASCII or UTF-8 string commands (`"DEPLOY"`). |
| `HEARTBEAT` | *None* | *None* | 0 bytes | Empty payload. Used strictly for ping/keep-alive routing. |

> *Note: Types like `GPS`, `IMU`, `SYS_STATE`, and `EVENT` currently do not strictly enforce a universal struct in the core parser. You can freely `memcpy` your own struct mapping for these.*

## Device Addressing & Broadcasting
Every packet encapsulates a `Sender_ID` and a `Receiver_ID` allowing you to strictly route telemetry between multiple rockets and ground stations.
- Set the `Receiver_ID` to `0xFF` (which is mapped to `Packet::BROADCAST_ID` / `Packet.BROADCAST_ID` in Python) if you want all listening ground stations/nodes to process the packet.
- When un-packing, use the builtin boolean check `rx.is_targeted_to(YOUR_ID)` to safely filter out noise intended for other modules!

## Usage Guide (C++)

Include `edlora.h` and `edlora.cpp` in your ESP-IDF or Arduino project.

```cpp
#include "edlora.h"

using namespace edlora;

void loop() {
    Packet tx_packet;
    tx_packet.sender_id = 0x10;
    tx_packet.receiver_id = 0xFF; // Broadcast
    tx_packet.msg_type = MsgType::GPS;
    tx_packet.seq_num = 1;

    // Option 1: Send raw bytes
    // tx_packet.payload_len = 4;
    // tx_packet.payload[0] = 0xDE;
    // tx_packet.payload[1] = 0xAD;
    // tx_packet.payload[2] = 0xBE;
    // tx_packet.payload[3] = 0xEF;

    // Option 2: Send strings effortlessly
    tx_packet.set_payload_string("Rocket Stage 1 separated!");

    // Optional Crypto:
    // crypto::XorCipher cipher(0xAA);
    // cipher.process(tx_packet);

    // Pack for transmission
    uint8_t tx_buffer[256];
    int packed_size = Protocol::pack(tx_packet, tx_buffer, sizeof(tx_buffer));

    if (packed_size > 0) {
        // Send tx_buffer[0 ... packed_size-1] over your LoRa modem
        // LoRa.beginPacket();
        // LoRa.write(tx_buffer, packed_size);
        // LoRa.endPacket();
    }
}

// Example: Receiving & Acknowledging in C++
void receive_example(uint8_t* rx_buffer, size_t length) {
    Packet rx_packet;
    
    // Unpack incoming bytes
    if (Protocol::unpack(rx_buffer, length, rx_packet)) {
        if (rx_packet.is_targeted_to(0x10)) {
            // Use your received data!
            if (rx_packet.msg_type == MsgType::COMMAND) {
                // Execute command...
                
                // Construct an automated ACK payload and pack it
                Packet ack = rx_packet.create_ack(0x10, millis());
                
                uint8_t reply_buf[256];
                int reply_len = Protocol::pack(ack, reply_buf, sizeof(reply_buf));
                // LoRa.write(reply_buf, reply_len);
            }
        }
    }
}
```

## Usage Guide (Python)

```python
from edlora import Packet, MsgType
from edlora_crypto import XorCipher

# Assume `rx_bytes` is the raw byte array received from Ground Station LoRa
rx_bytes = b'\xed\x02\x00\x10\xff\x04\x01\x00\x00\x00\x00\x04\xde\xad\xbe\xef\x00\xb1'

try:
    packet = Packet.unpack(rx_bytes)
    
    # Optional Crypto decoding:
    # cipher = XorCipher(0xAA)
    # packet = cipher.process(packet)
    
    # Retrieve raw bytes
    print(f"Payload (Bytes): {packet.payload}")
    
    # Retrieve as a decoded string
    print(f"Payload (String): {packet.get_payload_string()}")
    
    # Check Timestamp
    print(f"Time (ms): {packet.timestamp}")
except ValueError as e:
    print(f"Packet corrupted or rejected: {e}")


# Example: Unpacking specific message types
import struct
from edlora import Packet

p = Packet.unpack(rx_bytes) # Automatically validates sync byte and CRC16

# Extract targeted or broadcast addressing
is_for_me = p.is_targeted_to(0x01) 

if p.msg_type == MsgType.ALTIMETER:
    alt_cm, pressure_pa = struct.unpack("<iI", p.payload)
    print(f"Altimeter: {alt_cm / 100.0}m, {pressure_pa}Pa")
elif p.msg_type == MsgType.VELOCITY:
    vz_ms10, = struct.unpack("<h", p.payload)
    print(f"Velocity: {vz_ms10 / 10.0}m/s")
elif p.msg_type == MsgType.ACK:
    print(f"Received ACK for Sequence Number: {p.payload[0]}")
```


### Serial Monitor (CLI)
You can directly stream incoming data out of a physical LoRa module connected via USB using the `cli_monitor.py` example script. It fully handles framing raw serial bytes into complete Packets.

```bash
pip install pyserial
python3 examples/cli_monitor.py --port /dev/ttyUSB0 --baud 115200
```
*Outputs formatted logs: `[15:30:22.123] [0x10] [ALTIMETER] [BROADCAST] Altitude: 1500.5m, Pressure: 101325Pa`*

# Example: Transmitting from Python
```python
tx_packet = Packet(
    sender_id=0xFF,   # Ground station ID
    receiver_id=0x10, # Rocket ID
    msg_type=MsgType.COMMAND,
    seq_num=42,
    timestamp=12584   # Milliseconds
)

tx_packet.set_payload_string("DEPLOY PARACHUTE")
bytes_to_send = tx_packet.pack()

# Send `bytes_to_send` over your serial/USB LoRa module!
# serial_port.write(bytes_to_send)
```
