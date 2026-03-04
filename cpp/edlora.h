#ifndef EDLORA_H
#define EDLORA_H

#include <stdint.h>
#include <stddef.h>

namespace edlora {

constexpr uint8_t SYNC_BYTE = 0xED;
constexpr size_t MAX_PAYLOAD_SIZE = 240;
constexpr size_t HEADER_SIZE = 10; // Sync(1) + Sender(1) + Receiver(1) + Type(1) + Seq(1) + Timestamp(4) + Len(1)
constexpr size_t FOOTER_SIZE = 2; // CRC16

enum class MsgType : uint8_t {
    HEARTBEAT = 0x00,
    GPS = 0x01,
    ALTIMETER = 0x02,
    IMU = 0x03,
    COMMAND = 0x04,
    SYS_STATE = 0x05,   // E.g., Battery level, temperature, flight phase
    ORIENTATION = 0x06, // Quaternions or Euler angles
    EVENT = 0x07,       // Flight events (Launch, Apogee, Deployments)
    VELOCITY = 0x08,    // Vertical velocity (int16_t, m/s * 10)
    ACK = 0xFD,         // Command Acknowledgement (payload = original seq_num)
    ERROR_MSG = 0xFE,   // Error/Fault conditions
    CUSTOM = 0xFF
};

struct Packet {
    uint8_t sender_id;
    uint8_t receiver_id;
    MsgType msg_type;
    uint8_t seq_num;
    uint32_t timestamp; 
    uint8_t payload_len;
    uint8_t payload[MAX_PAYLOAD_SIZE];

    static constexpr uint8_t BROADCAST_ID = 0xFF;

    Packet();

    // Check if the packet is targeted to my_id, or is a broadcast
    bool is_targeted_to(uint8_t my_id) const;

    // Helper to generate an ACK packet for this specific message.
    // The payload of the generated ACK is simply the `seq_num` of this packet.
    Packet create_ack(uint8_t my_id, uint32_t current_timestamp) const;

    // Helper to set string payloads easily
    void set_payload_string(const char* str);
    
    // Helper to print/get payload as a null-terminated string (requires an external buffer)
    // Returns the number of characters copied.
    size_t get_payload_string(char* out_buffer, size_t out_buffer_size) const;
};

class Protocol {
public:
    // Pack packet into a buffer. Returns the exact number of bytes written or -1 on error.
    static int pack(const Packet& packet, uint8_t* buffer, size_t buffer_size);

    // Unpack a complete binary buffer to a Packet. Returns true if valid and CRC matches.
    static bool unpack(const uint8_t* buffer, size_t length, Packet& packet);

    // Calculate CRC-16 CCITT (0x1021 polynomial, initial 0xFFFF)
    static uint16_t calculate_crc(const uint8_t* data, size_t length);
};

} // namespace edlora

#endif // EDLORA_H
