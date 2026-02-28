#include <iostream>
#include <iomanip>
#include <cstring>
#include <thread>
#include <chrono>
#include "edlora.h"

using namespace edlora;

uint8_t seq_num = 0;
const uint8_t SENDER_ID = 0x10;
const uint8_t RECEIVER_ID = 0xFF;

void print_hex(const uint8_t* data, size_t length) {
    for (size_t i = 0; i < length; ++i) {
        std::cout << std::hex << std::setw(2) << std::setfill('0') << (int)data[i];
    }
}

void send_log(const char* msg) {
    Packet p;
    p.sender_id = SENDER_ID;
    p.receiver_id = RECEIVER_ID;
    p.msg_type = MsgType::COMMAND;
    p.seq_num = seq_num++;
    
    p.set_payload_string(msg);
    
    uint8_t buffer[256];
    int size = Protocol::pack(p, buffer, sizeof(buffer));
    
    // Simulate Reception: unpack the buffer
    Packet rx_p;
    if (Protocol::unpack(buffer, size, rx_p)) {
        char rx_msg[256];
        rx_p.get_payload_string(rx_msg, sizeof(rx_msg));
        std::cout << "[RX: COMMAND] '" << rx_msg << "' (Sequence: " << (int)rx_p.seq_num << ")" << std::endl;
    } else {
        std::cout << "[RX: COMMAND] ERROR UNPACKING" << std::endl;
    }
    
    std::this_thread::sleep_for(std::chrono::milliseconds(1000));
}

void send_telemetry(float alt, float vel) {
    Packet p;
    p.sender_id = SENDER_ID;
    p.receiver_id = RECEIVER_ID;
    p.msg_type = MsgType::ALTIMETER;
    p.seq_num = seq_num++;
    
    p.payload_len = 8;
    std::memcpy(&p.payload[0], &alt, sizeof(float));
    std::memcpy(&p.payload[4], &vel, sizeof(float));
    
    uint8_t buffer[256];
    int size = Protocol::pack(p, buffer, sizeof(buffer));
    
    // Simulate Reception: Unpack
    Packet rx_p;
    if (Protocol::unpack(buffer, size, rx_p) && rx_p.payload_len == 8) {
        float rx_alt, rx_vel;
        std::memcpy(&rx_alt, &rx_p.payload[0], sizeof(float));
        std::memcpy(&rx_vel, &rx_p.payload[4], sizeof(float));
        
        std::cout << "[RX: TELEM  ] Alt: " << std::fixed << std::setprecision(1) << rx_alt 
                  << "m, Vel: " << rx_vel << "m/s (Sequence: " << (int)rx_p.seq_num << ")" << std::endl;
    } else {
        std::cout << "[RX: TELEM  ] ERROR UNPACKING" << std::endl;
    }
    
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
}

int main() {
    std::cout << "=== edLoRa Rocket Flight Simulation (C++) ===" << std::endl;
    
    // 1. Idle
    send_log("SYSTEM INIT. AWAITING LAUNCH.");
    for (int i=0; i<3; ++i) send_telemetry(0.0f, 0.0f);
    
    // 2. Boost
    send_log("IGNITION! Liftoff detected.");
    float alt = 0.0f, vel = 0.0f;
    for (int i=0; i<5; ++i) {
        vel += 80.0f;
        alt += vel * 0.5f;
        send_telemetry(alt, vel);
    }
    
    // 3. Coast
    send_log("MECO. Coasting to Apogee.");
    while (vel > 0) {
        vel -= 9.8f;
        alt += vel * 0.5f;
        if (vel < 0) vel = 0;
        send_telemetry(alt, vel);
    }
    
    // 4. Recovery
    send_log("APOGEE REACHED. Deploying Drogue Parachute.");
    vel = -25.0f;
    for (int i=0; i<3; ++i) {
        alt += vel * 0.5f;
        send_telemetry(alt, vel);
    }
    
    send_log("ALTITUDE 500m. Deploying Main Parachute.");
    vel = -5.0f;
    while (alt > 0) {
        alt += vel * 0.5f;
        if (alt <= 0) alt = 0;
        send_telemetry(alt, vel);
    }
    
    send_log("TOUCHDOWN CONFIRMED. Waiting for recovery.");
    send_telemetry(0.0f, 0.0f);
    
    return 0;
}
