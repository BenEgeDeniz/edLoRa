#include <iostream>
#include <vector>
#include <string>
#include <cstring>
#include "edlora.h"
#include "edlora_crypto.h"

using namespace edlora;

int tests_passed = 0;
int tests_failed = 0;

#define ASSERT_TRUE(condition, name) \
    if (condition) { \
        std::cout << "[PASS] " << name << std::endl; \
        tests_passed++; \
    } else { \
        std::cout << "[FAIL] " << name << " (Line " << __LINE__ << ")" << std::endl; \
        tests_failed++; \
    }

void test_basic_packing() {
    Packet tx;
    tx.sender_id = 0x10;
    tx.receiver_id = 0x20;
    tx.msg_type = MsgType::HEARTBEAT;
    tx.seq_num = 5;
    
    uint8_t buffer[256];
    int size = Protocol::pack(tx, buffer, sizeof(buffer));
    
    ASSERT_TRUE(size == 8, "Basic Packing Size (0 payload)");
    ASSERT_TRUE(buffer[0] == SYNC_BYTE, "Sync Byte OK");
    
    Packet rx;
    bool success = Protocol::unpack(buffer, size, rx);
    ASSERT_TRUE(success, "Basic Unpacking Success");
    ASSERT_TRUE(rx.sender_id == 0x10, "Sender ID Match");
}

void test_string_payload() {
    Packet tx;
    tx.set_payload_string("TEST STRING");
    
    uint8_t buffer[256];
    int size = Protocol::pack(tx, buffer, sizeof(buffer));
    
    Packet rx;
    Protocol::unpack(buffer, size, rx);
    
    char out[256];
    rx.get_payload_string(out, sizeof(out));
    ASSERT_TRUE(std::string(out) == "TEST STRING", "String Payload Match");
}

void test_crc_failure() {
    Packet tx;
    tx.set_payload_string("CORRUPT ME");
    
    uint8_t buffer[256];
    int size = Protocol::pack(tx, buffer, sizeof(buffer));
    
    buffer[7] ^= 0xFF; // Flip bits in payload
    
    Packet rx;
    bool success = Protocol::unpack(buffer, size, rx);
    ASSERT_TRUE(!success, "CRC Failure Detected");
}

void test_crypto_wrapper() {
    Packet tx;
    tx.set_payload_string("SECRET MESSAGE");
    
    crypto::XorCipher cipher(0xAA);
    cipher.process(tx);
    
    uint8_t buffer[256];
    int size = Protocol::pack(tx, buffer, sizeof(buffer));
    
    Packet rx;
    Protocol::unpack(buffer, size, rx);
    
    cipher.process(rx); // Decrypt
    
    char out[256];
    rx.get_payload_string(out, sizeof(out));
    ASSERT_TRUE(std::string(out) == "SECRET MESSAGE", "Crypto Wrapper Match");
}

void test_stream_fragmentation() {
    Packet tx;
    tx.sender_id = 0xAA;
    tx.set_payload_string("FULL");
    
    uint8_t valid_bytes[256];
    int valid_size = Protocol::pack(tx, valid_bytes, sizeof(valid_bytes));
    
    // Simulate HALFPACKET + FULLPACKET + HALFPACKET
    std::vector<uint8_t> stream;
    
    // Insert half packet
    for (int i=0; i<4; i++) stream.push_back(valid_bytes[i]);
    
    // Insert full packet
    for (int i=0; i<valid_size; i++) stream.push_back(valid_bytes[i]);
    
    // Insert half packet
    for (int i=0; i<5; i++) stream.push_back(valid_bytes[i]);
    
    // Scanning Logic
    bool recovered = false;
    Packet rx;
    for (size_t i = 0; i < stream.size(); i++) {
        if (stream[i] == SYNC_BYTE) {
            // Attempt unpack
            if (Protocol::unpack(&stream[i], stream.size() - i, rx)) {
                recovered = true;
                break;
            }
        }
    }
    
    ASSERT_TRUE(recovered, "Recovered from fragmented stream");
    
    char out[256];
    rx.get_payload_string(out, sizeof(out));
    ASSERT_TRUE(std::string(out) == "FULL", "Fragmented Payload Intact");
}

int main() {
    std::cout << "=== Running edLoRa C++ Unit Tests ===" << std::endl;
    
    test_basic_packing();
    test_string_payload();
    test_crc_failure();
    test_crypto_wrapper();
    test_stream_fragmentation();
    
    std::cout << "---" << std::endl;
    std::cout << "Passed: " << tests_passed << ", Failed: " << tests_failed << std::endl;
    
    return (tests_failed == 0) ? 0 : 1;
}
