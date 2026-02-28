import time
import struct
from edlora import Packet, MsgType

def simulate_flight():
    print("=== edLoRa Rocket Flight Simulation ===")
    
    sender = 0x10 # Rocket
    receiver = 0xFF # Broadcast to all Ground Stations
    seq = 0
    
    def send_log(msg: str):
        nonlocal seq
        p = Packet(sender, receiver, MsgType.COMMAND, seq)
        p.set_payload_string(msg)
        packed = p.pack()
        seq += 1
        
        # Unpack the just-packed dataset for demonstration
        rx_p = Packet.unpack(packed)
        recovered_msg = rx_p.get_payload_string()
        print(f"[RX: COMMAND] '{recovered_msg}' (Sequence: {rx_p.seq_num})")
        time.sleep(1)

    def send_telemetry(alt: float, vel: float):
        nonlocal seq
        p = Packet(sender, receiver, MsgType.ALTIMETER, seq)
        # Pack two floats (Altitude, Velocity) into 8 bytes
        p.payload = struct.pack("<ff", alt, vel)
        packed = p.pack()
        seq += 1
        
        # Unpack the telemetry for demonstration
        rx_p = Packet.unpack(packed)
        recovered_alt, recovered_vel = struct.unpack("<ff", rx_p.payload)
        print(f"[RX: TELEM  ] Alt: {recovered_alt:.1f}m, Vel: {recovered_vel:.1f}m/s (Sequence: {rx_p.seq_num})")
        time.sleep(0.5)

    # 1. Pad / Idle
    send_log("SYSTEM INIT. AWAITING LAUNCH.")
    for _ in range(3):
        send_telemetry(0.0, 0.0)

    # 2. Ignition & Boost
    send_log("IGNITION! Liftoff detected.")
    alt, vel = 0.0, 0.0
    for _ in range(5):
        vel += 80.0 # accelerating
        alt += vel * 0.5
        send_telemetry(alt, vel)

    # 3. Motor Burnout & Coast
    send_log("MECO. Coasting to Apogee.")
    while vel > 0:
        vel -= 9.8 # gravity
        alt += vel * 0.5
        if vel < 0: vel = 0
        send_telemetry(alt, vel)

    # 4. Apogee & Recovery
    send_log("APOGEE REACHED. Deploying Drogue Parachute.")
    vel = -25.0
    for _ in range(3):
        alt += vel * 0.5
        send_telemetry(alt, vel)
        
    send_log("ALTITUDE 500m. Deploying Main Parachute.")
    vel = -5.0
    while alt > 0:
        alt += vel * 0.5
        if alt <= 0: alt = 0
        send_telemetry(alt, vel)
        
    send_log("TOUCHDOWN CONFIRMED. Waiting for recovery.")
    send_telemetry(0.0, 0.0)
    
if __name__ == "__main__":
    simulate_flight()
