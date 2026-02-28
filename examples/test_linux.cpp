#include <iostream>
#include <iomanip>
#include "edlora.h"

using namespace edlora;

void print_hex(const uint8_t* data, size_t length) {
    for (size_t i = 0; i < length; ++i) {
        std::cout << std::hex << std::setw(2) << std::setfill('0') << (int)data[i] << " ";
    }
    std::cout << std::dec << std::endl;
}

int main() {
    Packet tx_packet;
    tx_packet.sender_id = 0x10;
    tx_packet.receiver_id = 0xFF; // Broadcast
    tx_packet.msg_type = MsgType::GPS;
    tx_packet.seq_num = 1;

    // Test string helper
    tx_packet.set_payload_string("Hello LoRa!");

    uint8_t buffer[256];
    int packed_size = Protocol::pack(tx_packet, buffer, sizeof(buffer));

    if (packed_size < 0) {
        std::cerr << "Failed to pack packet!" << std::endl;
        return 1;
    }

    std::cout << "Packed " << packed_size << " bytes:" << std::endl;
    print_hex(buffer, packed_size);

    Packet rx_packet;
    bool unpacked = Protocol::unpack(buffer, packed_size, rx_packet);

    if (!unpacked) {
        std::cerr << "Failed to unpack packet!" << std::endl;
        return 1;
    }

    std::cout << "Unpacked successfully:" << std::endl;
    std::cout << "Sender: 0x" << std::hex << (int)rx_packet.sender_id << std::endl;
    std::cout << "Receiver: 0x" << std::hex << (int)rx_packet.receiver_id << std::endl;
    std::cout << "MsgType: 0x" << std::hex << (int)rx_packet.msg_type << std::endl;
    std::cout << "SeqNum: " << std::dec << (int)rx_packet.seq_num << std::endl;
    std::cout << "Payload Len: " << (int)rx_packet.payload_len << std::endl;
    std::cout << "Payload (HEX): ";
    print_hex(rx_packet.payload, rx_packet.payload_len);
    
    char str_buffer[256];
    rx_packet.get_payload_string(str_buffer, sizeof(str_buffer));
    std::cout << "Payload (STR): " << str_buffer << std::endl;

    return 0;
}
