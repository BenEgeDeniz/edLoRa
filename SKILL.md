---
name: edLoRa Python
description: A complete guide to using the edLoRa protocol library in Python.
---

# edLoRa Python Skill

The `edlora` library is a Python library for ground stations communicating with rockets using the edLoRa binary protocol. 

## Key Classes and Enums (from `edlora`)

### `MsgType` Enum
Defines the structure and intention of the message payload:
- `MsgType.HEARTBEAT` (0x00)
- `MsgType.GPS` (0x01)
- `MsgType.ALTIMETER` (0x02)
- `MsgType.IMU` (0x03)
- `MsgType.COMMAND` (0x04)
- `MsgType.SYS_STATE` (0x05)
- `MsgType.ORIENTATION` (0x06)
- `MsgType.EVENT` (0x07)
- `MsgType.ACK` (0xFD)
- `MsgType.ERROR_MSG` (0xFE)
- `MsgType.CUSTOM` (0xFF)

### `Packet` Class
The core data structure encapsulating a message. It handles the framing, validation, and payload.

**Constants:**
- `Packet.SYNC_BYTE = 0xED`
- `Packet.BROADCAST_ID = 0xFF`
- `Packet.MAX_PAYLOAD_SIZE = 240`

**Initialization:**
```python
from edlora import Packet, MsgType

packet = Packet(
    sender_id=0,               # ID of sender (0-255)
    receiver_id=0,             # Target ID or 0xFF for broadcast (0-255)
    msg_type=MsgType.CUSTOM,   # The message type (MsgType enum)
    seq_num=0,                 # Packet sequence number (0-255)
    timestamp=0,               # Timestamp in milliseconds (32-bit uint)
    payload=b""                # Raw payload bytes
)
```

**Packing & Unpacking (Binary Serialization):**
- `packet.pack() -> bytes`
  Returns the full packet bytes ready for transmission, including sync byte, header, payload, and the Little Endian CRC16 checksum. Validates fields before packing.
- `Packet.unpack(buffer: bytes) -> Packet`
  Class method that parses received bytes back into a `Packet` object. Automatically validates the `SYNC_BYTE`, payload length, and the CRC16 checksum. Raises `ValueError` on bad packets.

**Helpful Methods:**
- `packet.is_targeted_to(my_id: int) -> bool`
  Checks if the packet `receiver_id` matches `my_id` or `0xFF` (broadcast).
- `packet.create_ack(my_id: int, current_timestamp: int) -> Packet`
  Generates an acknowledgment packet targeted back to the sender containing the original `seq_num` as a 1-byte payload.
- `packet.set_payload_string(text: str)`
  Encodes a UTF-8 string directly into the payload bytes, truncating to `MAX_PAYLOAD_SIZE`.
- `packet.get_payload_string() -> str`
  Decodes the payload bytes back to a UTF-8 string (uses `errors='replace'`).

### `XorCipher` Class
A lightweight cryptographic cipher for obfuscating payloads.
```python
from edlora.crypto import XorCipher 
# Note: depending on imports, it might also be accessed as `from edlora_crypto import XorCipher` as shown in README docs.

cipher = XorCipher(key=0xAA)
encrypted_packet = cipher.process(packet) # Processes payload IN-PLACE
```
*`process()` mutates `packet.payload` and returns the same `packet` object.*

## Common Workflows

### 1. Transmitting a Packet
```python
import time
from edlora import Packet, MsgType

# 1. Create a packet
tx_packet = Packet(
    sender_id=0xFF,   # Ground Station ID
    receiver_id=0x10, # Target Rocket ID
    msg_type=MsgType.COMMAND,
    seq_num=42,
    timestamp=int(time.time() * 1000) % 0xFFFFFFFF
)

# 2. Set the payload
tx_packet.set_payload_string("DEPLOY PARACHUTE")

# 3. Get bytes for transmission
bytes_to_send = tx_packet.pack()

# Write `bytes_to_send` to your serial/USB LoRa module
# serial_port.write(bytes_to_send)
```

### 2. Receiving and Processing Packets
```python
from edlora import Packet, MsgType
import struct

# Receive raw bytes from your LoRa module
# rx_bytes = serial_port.read(...)

try:
    packet = Packet.unpack(rx_bytes)
except ValueError as e:
    # Handle corrupted, partial, or malformed packets (wrong CRC, sync byte missing)
    print(f"Packet corrupted or rejected: {e}")
    return
    
if packet.is_targeted_to(0xFF): # Check if message is broadcase or meant for Ground Station (0xFF)
    print(f"Received {packet.msg_type.name} from ID={packet.sender_id}")
    
    # Process known types
    if packet.msg_type == MsgType.ALTIMETER:
        # Example decoding an Altimeter payload (assuming two C-struct float32 values)
        alt, vel = struct.unpack("<ff", packet.payload)
        print(f"Altitude: {alt}m, Velocity: {vel}m/s")
        
    elif packet.msg_type == MsgType.COMMAND:
        command_str = packet.get_payload_string()
        print(f"Command received: {command_str}")
        
    elif packet.msg_type == MsgType.ACK:
        print(f"Received ACK for Sequence Number: {packet.payload[0]}")
```

### 3. Handling Acknowledgments (ACKs)
When you receive a command, you often want to send a bounce back ACK automatically:
```python
if packet.msg_type == MsgType.COMMAND:
    # Process command ...
    
    # Generate ACK
    ack_packet = packet.create_ack(my_id=0xFF, current_timestamp=int(time.time()*1000)%0xFFFFFFFF)
    
    # Send ACK back down the pipe
    # serial_port.write(ack_packet.pack())
```

### 4. Adding Cryptography (XorCipher)
```python
from edlora import Packet
from edlora.crypto import XorCipher

# Shared secret key (0-255)
cipher = XorCipher(0xAA)

# Encrypting before transmit
tx_packet = Packet(...)
cipher.process(tx_packet) # Modifies tx_packet payload in place
bytes_tx = tx_packet.pack()

# Decrypting after receive
rx_packet = Packet.unpack(rx_bytes)
cipher.process(rx_packet) # Modifies rx_packet payload in place
print(rx_packet.get_payload_string())
```
