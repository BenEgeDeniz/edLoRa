#include "edlora.h"

namespace edlora {

Packet::Packet() 
    : version(PROTOCOL_VERSION), flags(0), sender_id(0), receiver_id(0), msg_type(MsgType::CUSTOM), seq_num(0), 
      timestamp(0), payload_len(0) {
    for (size_t i = 0; i < MAX_PAYLOAD_SIZE; ++i) {
        payload[i] = 0;
    }
}

bool Packet::is_targeted_to(uint8_t my_id) const {
    return (receiver_id == my_id) || (receiver_id == BROADCAST_ID);
}

Packet Packet::create_ack(uint8_t my_id, uint32_t current_timestamp) const {
    Packet ack_p;
    ack_p.sender_id = my_id;
    ack_p.receiver_id = this->sender_id; // Return to sender
    ack_p.msg_type = MsgType::ACK;
    ack_p.seq_num = 0; // ACKs don't strictly need their own sequences
    ack_p.timestamp = current_timestamp;
    
    // Payload is exactly 1 byte: the original sequence number
    ack_p.payload_len = 1;
    ack_p.payload[0] = this->seq_num;
    
    return ack_p;
}

void Packet::set_payload_string(const char* str) {
    if (str == nullptr) return;
    
    #ifdef _WIN32
    size_t length = strnlen_s(str, MAX_PAYLOAD_SIZE);
    #else
    // Some older systems don't have strnlen, so we manually do a bounded check 
    // to be extra safe without relying on libc.
    size_t length = 0;
    while(length < MAX_PAYLOAD_SIZE && str[length] != '\0') {
        length++;
    }
    #endif

    for (size_t i = 0; i < length; ++i) {
        payload[i] = static_cast<uint8_t>(str[i]);
    }
    payload_len = static_cast<uint8_t>(length);
}

size_t Packet::get_payload_string(char* out_buffer, size_t out_buffer_size) const {
    if (out_buffer == nullptr || out_buffer_size == 0) return 0;

    size_t copy_len = payload_len;
    if (copy_len >= out_buffer_size) {
        copy_len = out_buffer_size - 1; // leave room for null terminator
    }

    for (size_t i = 0; i < copy_len; ++i) {
        out_buffer[i] = static_cast<char>(payload[i]);
    }
    out_buffer[copy_len] = '\0';
    
    return copy_len;
}

int Protocol::pack(const Packet& packet, uint8_t* buffer, size_t buffer_size) {
    if (buffer == nullptr) return -1;
    
    size_t required_size = HEADER_SIZE + packet.payload_len + FOOTER_SIZE;
    if (buffer_size < required_size) return -1;
    if (packet.payload_len > MAX_PAYLOAD_SIZE) return -1;

    // Header
    buffer[0] = SYNC_BYTE;
    buffer[1] = packet.version;
    buffer[2] = packet.flags;
    buffer[3] = packet.sender_id;
    buffer[4] = packet.receiver_id;
    buffer[5] = static_cast<uint8_t>(packet.msg_type);
    buffer[6] = packet.seq_num;
    
    // Timestamp (4 bytes, Little Endian)
    buffer[7] = static_cast<uint8_t>(packet.timestamp & 0xFF);
    buffer[8] = static_cast<uint8_t>((packet.timestamp >> 8) & 0xFF);
    buffer[9] = static_cast<uint8_t>((packet.timestamp >> 16) & 0xFF);
    buffer[10] = static_cast<uint8_t>((packet.timestamp >> 24) & 0xFF);
    
    buffer[11] = packet.payload_len;

    // Payload
    for (size_t i = 0; i < packet.payload_len; ++i) {
        buffer[HEADER_SIZE + i] = packet.payload[i];
    }

    // CRC (Calculated over Header + Payload)
    uint16_t crc = calculate_crc(buffer, HEADER_SIZE + packet.payload_len);
    
    // Little-endian order for CRC
    buffer[HEADER_SIZE + packet.payload_len] = crc & 0xFF;
    buffer[HEADER_SIZE + packet.payload_len + 1] = (crc >> 8) & 0xFF;

    return static_cast<int>(required_size);
}

bool Protocol::unpack(const uint8_t* buffer, size_t length, Packet& packet) {
    if (buffer == nullptr || length < HEADER_SIZE + FOOTER_SIZE) return false;
    
    if (buffer[0] != SYNC_BYTE) return false;
    
    // Validate version here
    if (buffer[1] != PROTOCOL_VERSION) return false;

    uint8_t payload_len = buffer[11];
    if (length < HEADER_SIZE + payload_len + FOOTER_SIZE) return false;
    if (payload_len > MAX_PAYLOAD_SIZE) return false;

    // Verify CRC
    uint16_t received_crc = buffer[HEADER_SIZE + payload_len] | (buffer[HEADER_SIZE + payload_len + 1] << 8);
    uint16_t calculated_crc = calculate_crc(buffer, HEADER_SIZE + payload_len);
    
    if (received_crc != calculated_crc) return false;

    // Explicitly zero out the payload buffer first to prevent ghost data
    for (size_t i = 0; i < MAX_PAYLOAD_SIZE; ++i) {
        packet.payload[i] = 0;
    }

    // Populate Packet
    packet.version = buffer[1];
    packet.flags = buffer[2];
    packet.sender_id = buffer[3];
    packet.receiver_id = buffer[4];
    packet.msg_type = static_cast<MsgType>(buffer[5]);
    packet.seq_num = buffer[6];
    
    packet.timestamp = static_cast<uint32_t>(buffer[7]) |
                       (static_cast<uint32_t>(buffer[8]) << 8) |
                       (static_cast<uint32_t>(buffer[9]) << 16) |
                       (static_cast<uint32_t>(buffer[10]) << 24);
                       
    packet.payload_len = payload_len;

    for (size_t i = 0; i < payload_len; ++i) {
        packet.payload[i] = buffer[HEADER_SIZE + i];
    }

    return true;
}

uint16_t Protocol::calculate_crc(const uint8_t* data, size_t length) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < length; ++i) {
        crc ^= (uint16_t)data[i] << 8;
        for (uint8_t j = 0; j < 8; ++j) {
            if (crc & 0x8000) {
                crc = (crc << 1) ^ 0x1021;
            } else {
                crc <<= 1;
            }
        }
    }
    return crc;
}

} // namespace edlora
