# edLoRa Protocol
[![PyPI version](https://badge.fury.io/py/edlora.svg)](https://pypi.org/project/edlora/)

A lightweight, cross-language (C++ & Python) binary protocol designed specifically for rocketry telemetry and command data over LoRa modules. Supports both standard Linux and ESP32 platforms in C++, and comes with a Python 3 ground station implementation.

## Features
- **Binary Packing:** Completely avoids string processing to keep LoRa bandwidth usage minimal.
- **Robust Framing:** Dedicated sync bytes, payload length checking, and CCITT CRC-16 checksums ensure data integrity even on noisy RF channels.
- **Multi-node addressing:** Includes `Sender ID` and `Receiver ID` (with `0xFF` reserved for Broadcast).
- **Message Types:** Differentiates traffic types (e.g., GPS, IMU, Altimeter, Commands).
- **Embedded Friendly:** The C++ implementation avoids dynamic memory allocation entirely, protecting against heap fragmentation on ESP32/Arduino.
- **Optional Crypto:** Includes a lightweight XOR-cipher wrapper inside `edlora_crypto` for obfuscating payload bytes. (Easily swappable with AES if actual cryptographic security is required).

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
| `ALTIMETER` | `0x02` | Altitude and velocity telemetry data. |
| `IMU` | `0x03` | Raw Accel, Gyro, Mag data. |
| `COMMAND` | `0x04` | Ground-to-vehicle commands or text logs. |
| `SYS_STATE` | `0x05` | System battery, temp, and current flight phase. |
| `ORIENTATION` | `0x06` | Calculated attitude (Quaternions/Euler angles). |
| `EVENT` | `0x07` | Major flight events (Liftoff, MECO, Apogee, Deployment). |
| `ERROR_MSG` | `0xFE` | Faults and system error states. |
| `CUSTOM` | `0xFF` | Freeform binary payloads. |

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

// Example: Receiving in C++
void receive_example(uint8_t* rx_buffer, size_t length) {
    Packet rx_packet;
    
    // Unpack incoming bytes
    if (Protocol::unpack(rx_buffer, length, rx_packet)) {
        char str_buffer[256];
        rx_packet.get_payload_string(str_buffer, sizeof(str_buffer));
        
        // Use your received data!
        // Serial.printf("Received string: %s\n", str_buffer);
    }
}
```

## Usage Guide (Python)

```python
from edlora import Packet, MsgType
from edlora_crypto import XorCipher

# Assume `rx_bytes` is the raw byte array received from Ground Station LoRa
rx_bytes = b'\xed\x10\xff\x01\x01\x04\xde\xad\xbe\xef\x00\xb1'

try:
    packet = Packet.unpack(rx_bytes)
    
    # Optional Crypto decoding:
    # cipher = XorCipher(0xAA)
    # packet = cipher.process(packet)
    
    # Retrieve raw bytes
    print(f"Payload (Bytes): {packet.payload}")
    
    # Retrieve as a decoded string
    print(f"Payload (String): {packet.get_payload_string()}")
except ValueError as e:
    print(f"Packet corrupted or rejected: {e}")


# Example: Transmitting from Python
tx_packet = Packet(
    sender_id=0xFF,   # Ground station ID
    receiver_id=0x10, # Rocket ID
    msg_type=MsgType.COMMAND,
    seq_num=42
)

tx_packet.set_payload_string("DEPLOY PARACHUTE")
bytes_to_send = tx_packet.pack()

# Send `bytes_to_send` over your serial/USB LoRa module!
# serial_port.write(bytes_to_send)
```
