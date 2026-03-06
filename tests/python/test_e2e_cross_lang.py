import subprocess
import time
from edlora import Packet, MsgType

print("=== Starting End-to-End Integration Test (Python <-> C++) ===")

# Compile a quick C++ program that just outputs 3 raw binary packets to stdout
cpp_source = """
#include <iostream>
#include "edlora.h"
#include <unistd.h>
#include <chrono>
#include <cstring>

using namespace edlora;

uint64_t current_time() {
    return std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::system_clock::now().time_since_epoch()).count();
}

int main() {
    Packet p1;
    p1.sender_id = 0xAA;
    p1.receiver_id = 0xBB;
    p1.msg_type = MsgType::COMMAND;
    p1.seq_num = 1;
    p1.timestamp = current_time();
    p1.set_payload_string("E2E_TEST_1");

    Packet p2;
    p2.sender_id = 0xAA;
    p2.receiver_id = Packet::BROADCAST_ID;
    p2.msg_type = MsgType::ALTIMETER;
    p2.seq_num = 2;
    p2.timestamp = current_time() + 1000;
    
    int32_t alt_cm = 150050; // 1500.5m
    uint32_t press_pa = 101325;
    memcpy(p2.payload, &alt_cm, sizeof(int32_t));
    memcpy(p2.payload + 4, &press_pa, sizeof(uint32_t));
    p2.payload_len = 8;
    
    Packet p3;
    p3.sender_id = 0xAA;
    p3.receiver_id = Packet::BROADCAST_ID;
    p3.msg_type = MsgType::VELOCITY;
    p3.seq_num = 3;
    p3.timestamp = current_time() + 1000;
    
    int16_t vz = -200; // -20.0 m/s
    memcpy(p3.payload, &vz, sizeof(int16_t));
    p3.payload_len = 2;

    uint8_t buf[256];
    int len1 = Protocol::pack(p1, buf, sizeof(buf));
    std::cout.write(reinterpret_cast<char*>(buf), len1);
    
    int len2 = Protocol::pack(p2, buf, sizeof(buf));
    std::cout.write(reinterpret_cast<char*>(buf), len2);
    
    int len3 = Protocol::pack(p3, buf, sizeof(buf));
    std::cout.write(reinterpret_cast<char*>(buf), len3);
    
    return 0;
}
"""

with open("/tmp/e2e_test.cpp", "w") as f:
    f.write(cpp_source)

# Compile
subprocess.run([
    "g++", 
    "-I/home/benegedeniz/Desktop/edlora/cpp", 
    "-std=c++11",
    "/tmp/e2e_test.cpp", 
    "/home/benegedeniz/Desktop/edlora/cpp/edlora.cpp", 
    "-o", "/tmp/e2e_test_bin"
], check=True)

# Run C++ code and capture binary stdout
result = subprocess.run(["/tmp/e2e_test_bin"], capture_output=True)
raw_bytes = result.stdout

print(f"Captured {len(raw_bytes)} bytes from C++.")

# Parse in Python
offset = 0
packets = []
while offset < len(raw_bytes):
    if raw_bytes[offset] == Packet.SYNC_BYTE:
        # Minimum safe read to get payload len
        if offset + Packet.HEADER_SIZE > len(raw_bytes):
            break
            
        payload_len = raw_bytes[offset + 11]
        total_len = Packet.HEADER_SIZE + payload_len + Packet.FOOTER_SIZE
        
        try:
            packet = Packet.unpack(raw_bytes[offset:offset+total_len])
            packets.append(packet)
            offset += total_len
        except ValueError as e:
            offset += 1
    else:
        offset += 1

print(f"Successfully decoded {len(packets)} packets in Python.")
for i, p in enumerate(packets):
    print(f"[{i+1}] Sender: 0x{p.sender_id:02X}, Target: 0x{p.receiver_id:02X}, Seq: {p.seq_num}, Time: {p.timestamp}, Type: {p.msg_type.name}")

assert len(packets) == 3
assert packets[0].get_payload_string() == "E2E_TEST_1"
assert packets[0].msg_type == MsgType.COMMAND

assert packets[1].msg_type == MsgType.ALTIMETER
import struct
alt_cm, press_pa = struct.unpack("<iI", packets[1].payload)
assert alt_cm == 150050
assert press_pa == 101325

assert packets[2].msg_type == MsgType.VELOCITY
vz_ms10, = struct.unpack("<h", packets[2].payload)
assert vz_ms10 == -200

print("✅ E2E Python <-> C++ Protocol Packing Validation Complete!")
