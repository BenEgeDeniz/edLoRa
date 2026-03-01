# Getting Started with edLoRa

This guide will walk you through integrating `edLoRa` into both your C++ (Rocket/ESP32) and Python (Ground Station) environments.

## C++ Integration

### 1. Include the Header
Clone or copy the `edlora.h` and `edlora.cpp` files directly into your C++ or Arduino project map, and include it.
```cpp
#include "edlora.h"

using namespace edlora;
```

### 2. Creating & Packing a Packet
```cpp
Packet tx;
tx.sender_id = 0x10;             // Your Rocket ID
tx.receiver_id = 0xFF;           // Broadcast to all Ground Stations
tx.msg_type = MsgType::COMMAND;
tx.seq_num = 1;
tx.timestamp = millis();         // Record precisely when the event happened

tx.set_payload_string("SPARK_IGNITER");

uint8_t buffer[256];
int size = Protocol::pack(tx, buffer, sizeof(buffer));

if (size > 0) {
    // Send `buffer` with length `size` via your LoRa radio
    LoRa.beginPacket();
    LoRa.write(buffer, size);
    LoRa.endPacket();
}
```

### 3. Parsing Received Data
```cpp
// Assume `rx_buffer` contains bytes received from the LoRa modem
Packet rx;
if (Protocol::unpack(rx_buffer, rx_len, rx)) {
    // CRC is valid! Check if the packet is meant for us:
    if (rx.is_targeted_to(0x10)) { 
        // Process exactly like a struct
        if (rx.msg_type == MsgType::COMMAND) {
            // Execute command...
            
            // Instantly bounce an ACK back to the sender
            Packet ack_p = rx.create_ack(0x10, millis());
            
            uint8_t tx_buffer[256];
            int ack_len = Protocol::pack(ack_p, tx_buffer, sizeof(tx_buffer));
            // LoRa.write(tx_buffer, ack_len);
        }
    }
}
```

---

## Python Integration
Python integration is heavily utilized on Raspberry Pi or PC-based Ground Stations receiving data sequentially from serial modems.

### 1. Installation
The python library is available on PyPI.
```bash
pip install edlora
```

### 2. Basic Initialization
```python
from edlora import Packet, MsgType
import time

rocket_packet = Packet(
    sender_id=0x10,
    receiver_id=Packet.BROADCAST_ID,
    msg_type=MsgType.HEARTBEAT,
    seq_num=5,
    timestamp=int(time.time() * 1000) & 0xFFFFFFFF
)

# Convert to a binary bytearray securely ready for RF transmission
binary_data = rocket_packet.pack()
```

### 3. Reading and Unpacking
Unpacking throws `ValueError` safely instantly if the Buffer Length or `CRC-16` footprint fail.
```python
try:
    rx = Packet.unpack(binary_buffer_from_lora)
    
    # Analyze the data seamlessly 
    if rx.is_targeted_to(GROUND_STATION_ID):
        print(f"Packet verified. Offset time: {rx.timestamp}ms.")
        print(f"Raw Decode: {rx.get_payload_string()}")
        
        # If it was an ACK, the payload perfectly matches the seq_num of the command we sent!
        if rx.msg_type == MsgType.ACK:
            print(f"Rocket successfully acknowledged command #{rx.payload[0]}")

except ValueError as e:
    print(f"Bad packet dropped: {e}")
```
