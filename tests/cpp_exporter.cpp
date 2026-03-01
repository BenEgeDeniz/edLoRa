#include <iostream>
#include <iomanip>
#include <vector>
#include <string>
#include "../cpp/edlora.h"

// Note to compile: g++ cpp_exporter.cpp ../cpp/edlora.cpp -o cpp_exporter -std=c++11

using namespace edlora;

void print_hex(const uint8_t* buffer, size_t length) {
    for (size_t i = 0; i < length; ++i) {
        std::cout << std::hex << std::setw(2) << std::setfill('0') << (int)buffer[i];
    }
    std::cout << std::endl;
}

int main() {
    uint8_t buffer[512];
    
    // Test Case 1: Simple Heartbeat (No Payload)
    Packet p1;
    p1.sender_id = 42;
    p1.receiver_id = 100;
    p1.msg_type = MsgType::HEARTBEAT;
    p1.seq_num = 1;
    p1.timestamp = 0x11223344; // specific byte pattern
    
    int len1 = Protocol::pack(p1, buffer, sizeof(buffer));
    std::cout << "TEST1:";
    print_hex(buffer, len1);

    // Test Case 2: Custom Message with string Payload
    Packet p2;
    p2.sender_id = 255;
    p2.receiver_id = 0;
    p2.msg_type = MsgType::CUSTOM;
    p2.seq_num = 200;
    p2.timestamp = 0xFFEEDDCC;
    p2.set_payload_string("TEKNOFEST2026");
    
    int len2 = Protocol::pack(p2, buffer, sizeof(buffer));
    std::cout << "TEST2:";
    print_hex(buffer, len2);

    // Test Case 3: Binary Payload (Full Max Size)
    // Note: C++ has 0 initialized payload. Python script should replicate this.
    Packet p3;
    p3.sender_id = 1;
    p3.receiver_id = 2;
    p3.msg_type = MsgType::SYS_STATE;
    p3.seq_num = 255;
    p3.timestamp = 99999999;
    p3.payload_len = 240; // Max size
    for (int i=0; i<240; i++) {
        p3.payload[i] = i & 0xFF; // Pattern 0,1,2...239
    }
    
    int len3 = Protocol::pack(p3, buffer, sizeof(buffer));
    std::cout << "TEST3:";
    print_hex(buffer, len3);

    return 0;
}
