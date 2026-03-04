import time
import struct
from edlora import Packet, MsgType

def simulate_flight():
    print("=== edLoRa Rocket Flight Simulation ===")
    
    sender = 0x10 # Rocket
    broadcast_receiver = Packet.BROADCAST_ID # 0xFF
    ground_station = 0x01 # Our local listener ID
    seq = 0
    
    def send_log(msg: str):
        nonlocal seq
        # We target this specific ground station directly
        p = Packet(sender, ground_station, MsgType.COMMAND, seq)
        p.set_payload_string(msg)
        packed = p.pack()
        seq += 1
        
        # Unpack the just-packed dataset for demonstration
        rx_p = Packet.unpack(packed)
        if not rx_p.is_targeted_to(ground_station):
            return # Drop packets not meant for us

        recovered_msg = rx_p.get_payload_string()
        print(f"[RX: COMMAND] '{recovered_msg}' (Sequence: {rx_p.seq_num})")
        time.sleep(1)

    def send_telemetry(alt: float, vel: float):
        nonlocal seq
        # Telemetry is broadcasted to ALL listeners
        p = Packet(sender, broadcast_receiver, MsgType.ALTIMETER, seq)
        # Pack altitude and pressure into 8 bytes
        pressure_pa = 101325
        p.payload = struct.pack("<iI", int(alt * 100), pressure_pa)
        packed = p.pack()
        seq += 1
        
        # Unpack the telemetry for demonstration
        rx_p = Packet.unpack(packed)
        if rx_p.is_targeted_to(ground_station):
            recovered_alt_cm, recovered_pressure = struct.unpack("<iI", rx_p.payload)
            print(f"[RX: TELEM  ] Alt: {recovered_alt_cm / 100.0:.1f}m, Press: {recovered_pressure}Pa (Sequence: {rx_p.seq_num})")

        p_vel = Packet(sender, broadcast_receiver, MsgType.VELOCITY, seq)
        p_vel.payload = struct.pack("<h", int(vel * 10))
        packed_vel = p_vel.pack()
        seq += 1

        rx_p_vel = Packet.unpack(packed_vel)
        if rx_p_vel.is_targeted_to(ground_station):
            recovered_vel_ms10, = struct.unpack("<h", rx_p_vel.payload)
            print(f"[RX: TELEM  ] Vel: {recovered_vel_ms10 / 10.0:.1f}m/s (Sequence: {rx_p_vel.seq_num})")
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
