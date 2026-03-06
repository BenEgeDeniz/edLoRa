# edLoRa Architectural Decisions

This document outlines *why* the `edLoRa` protocol is structured the way it is, and the specific engineering challenges it solves within high-power rocketry telemetry.

## Why a Binary Protocol? (Instead of JSON/Text)

The most common mistake when building custom telemetry systems over LoRa is attempting to send JSON strings (e.g., `{"alt": 1500.5, "event": "apogee"}`).
1. **Bandwidth Limits:** LoRa relies on Chrip Spread Spectrum modulation. At high spread factors (SF10-12) for extreme range, your actual data rate might be less than 1 kilobyte per **second**. An 80-byte JSON string takes massive airtime compared to an equivalent 8-byte binary struct.
2. **Duty Cycles:** Many regions (like the EU) strictly enforce a 1% duty cycle. Meaning if a packet takes 1 second to transmit, the radio must be silent for 99 seconds. Binary minimizes 'Time-on-Air' (ToA).
3. **FIFO Limits:** The physical SX1276/SX1262 LoRa chips contain a hardcoded 256-byte hardware buffer. If you exceed this, you physically cannot send the packet without complex multi-packet chaining. `edLoRa` enforces a `MAX_PAYLOAD_SIZE` of 240, guaranteeing every packet easily fits the hardware limits.

## Why the `SYNC_BYTE`? (0xED)

If you have a Python ground station reading raw serial bytes from an Arduino receiver over USB, it is incredibly common for the Arduino to reset, drop bytes, or send half a stream. Your Python process will suddenly be looking at a random byte like `0x4F` when it expected the start of a packet.

The `SYNC_BYTE` (`0xED`) acts as a distinct "anchor." The unpacking algorithm simply skips and ignores all incoming bytes until it spots `0xED`. Once found, it validates the structure, extracts the payload length from the 12-byte header, and jumps directly to the CRC. If it was a false `0xED`, the CRC will fail, the packet is safely discarded, and the scanner resumes hunting for the next `0xED`.

## Why Version and Flags? (Protocol v2.0)

For long-term reliability and compatibility, the header strictly enforces a `version` byte. This means that if `edLoRa` v3.0 introduces a different byte structure tomorrow, existing v2 parsers won't crash; they will cleanly reject the packet, allowing you to maintain backwards-compatible parser trees.

The `flags` byte provides extreme power without eating bandwidth. Instead of creating redundant `MsgType`s like "ENCRYPTED_TELEMETRY" vs "RAW_TELEMETRY", a single bitmask determines if a packet requires an ACK, is fragmented, or has priority routing.

## Why Enums for `MsgType`?

Using a `uint8_t` (0-255) to define what a packet *means* allows the parser to instantly know how to unpack the payload blob, taking up only 1 single byte of bandwidth.

- `0x04` means "This is a Command".
- `0x02` means "This is Altimeter Data". 

This scales infinitely up to 255 unique message definitions without adding any string parsing overhead to the C++ flight computer.

## Why Sequence Numbers? (`seq_num`)

Wireless RF communication experiences packet loss. If a rocket is transmitting altimeter data every 100ms, and the ground station receives sequence `#42` and then `#45`, the ground station mathematics can instantly deduce that packets `#43` and `#44` were dropped due to RF interference or antenna nulls during a rocket roll. 
Without sequence numbers, the ground station has no concept of missed data.

## Why a 32-bit `timestamp`?

When flying at Mach 1, a delay of 200 milliseconds between transmission and ground-station reception can mean an altitude difference of hundreds of feet. 
If the ground station timestamps data using its *own* local CPU clock upon reception, all data metrics will be heavily time-shifted and inaccurate. 

By having the Rocket natively inject its internal `millis()` clock into every header, you can reconstruct the absolute perfect timeline of the flight post-launch, perfectly correlating events regardless of when the packet was actually received by the base station.

## Why CRC-16?

RF noise causes bit-flips. A `0` becomes a `1` while flying through the air.
A Cyclic Redundancy Check (CRC-16 CCITT) mathematically hashes the entire Header + Payload. When the packet arrives, the receiver re-calculates the hash. If even a single bit in the 254-byte stream was flipped by cosmic noise or interference, the hash completely changes and `unpack()` correctly rejects the corrupted data.
Using 16 bits provides significantly better guarantees than an 8-bit checksum for payloads reaching 240 bytes.

## The Acknowledgement (ACK) System

When a Ground Station sends a critical uplink (like `FIRE_PYRO`), knowing it actually arrived is paramount.
The `[MsgType::ACK]` (0xFD) elegantly solves this.
If the Rocket receives sequence `#84` (Command), it automatically strips the `#84` and places it inside the payload of a brand new packet aimed backwards at the Ground Station with type `ACK`. The Ground Station sees the `ACK` and reads `84` from the payload, physically proving the command executed securely.
