import sys
import time
import argparse
import struct
from datetime import datetime
from edlora import Packet, MsgType

try:
    import serial
except ImportError:
    print("Warning: pyserial is not installed. To read from actual hardware, run: pip install pyserial")
    serial = None

def format_packet(p: Packet) -> str:
    # [TIME]
    now = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    
    # [SENDER ID]
    sender_str = f"0x{p.sender_id:02X}"
    
    # [MSG_TYPE]
    msg_type_str = p.msg_type.name if isinstance(p.msg_type, MsgType) else f"0x{int(p.msg_type):02X}"
    
    # [BROADCAST OR TARGETED (to whom)]
    if p.receiver_id == Packet.BROADCAST_ID:
        target_str = "BROADCAST"
    else:
        target_str = f"TARGETED: 0x{p.receiver_id:02X}"
        
    # message content
    if p.msg_type == MsgType.COMMAND:
        content = f"'{p.get_payload_string()}'"
    elif p.msg_type == MsgType.ALTIMETER and p.payload_len >= 8:
        alt, vel = struct.unpack("<ff", p.payload[:8])
        content = f"Altitude: {alt:.2f}m, Velocity: {vel:.2f}m/s"
    elif p.msg_type == MsgType.HEARTBEAT:
        content = "Alive"
    else:
        content = f"Raw Hex: {p.payload.hex()}"
        
    return f"[{now}] [{sender_str}] [{msg_type_str}] [{target_str}] {content}"

def stream_from_serial(port: str, baud: int):
    if not serial:
        print("Cannot stream from serial because pyserial is missing.")
        return

    print(f"Opening Serial Port: {port} @ {baud} baud...")
    try:
        ser = serial.Serial(port, baud, timeout=1.0)
    except Exception as e:
        print(f"Error opening port: {e}")
        return

    print("Listening for edLoRa packets... (Press Ctrl+C to stop)")
    print("-" * 80)
    
    while True:
        try:
            # Framing Logic: Wait for SYNC_BYTE
            byte = ser.read(1)
            if not byte:
                continue
            
            if byte[0] == Packet.SYNC_BYTE:
                # Read the rest of the header (9 bytes)
                header_rest = ser.read(9)
                if len(header_rest) != 9:
                    continue
                
                payload_len = header_rest[8]
                
                # Check bounds to avoid hanging on bad data
                if payload_len > Packet.MAX_PAYLOAD_SIZE:
                    continue 

                # Read Payload and CRC (2 bytes)
                body_rest = ser.read(payload_len + Packet.FOOTER_SIZE)
                if len(body_rest) != payload_len + Packet.FOOTER_SIZE:
                    continue
                
                # Reconstruct full buffer and unpack
                full_packet_bytes = byte + header_rest + body_rest
                try:
                    p = Packet.unpack(full_packet_bytes)
                    print(format_packet(p))
                except ValueError as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [RAW DECODE ERROR] {e}")
                    
        except KeyboardInterrupt:
            print("\nStopping monitor...")
            break
        except Exception as e:
            print(f"Serial read error: {e}")
            time.sleep(1)

def main():
    parser = argparse.ArgumentParser(description="edLoRa CLI Streaming Monitor")
    parser.add_argument("--port", type=str, default="/dev/ttyUSB0", help="Serial port to listen on (e.g., /dev/ttyUSB0 or COM3)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate (default 115200)")
    parser.add_argument("--demo", action="store_true", help="Run in mock streaming demo mode (no hardware required)")
    
    args = parser.parse_args()
    
    if args.demo:
        print("Running in DEMO mode... generating fake packets.")
        seq = 0
        try:
            while True:
                time.sleep(1.5)
                # Generate a mock broadcast Altimeter packet
                p_alt = Packet(sender_id=0x10, receiver_id=Packet.BROADCAST_ID, msg_type=MsgType.ALTIMETER, seq_num=seq, timestamp=int(time.time() * 1000) & 0xFFFFFFFF)
                p_alt.payload = struct.pack("<ff", 1500.5 + seq, 20.3)
                print(format_packet(p_alt))
                
                # Alternate with a targeted command
                if seq % 3 == 0:
                    time.sleep(1)
                    p_cmd = Packet(sender_id=0x01, receiver_id=0x10, msg_type=MsgType.COMMAND, seq_num=seq, timestamp=int(time.time() * 1000) & 0xFFFFFFFF)
                    p_cmd.set_payload_string("DEPLOY MAIN CHUTE")
                    print(format_packet(p_cmd))
                
                seq += 1
        except KeyboardInterrupt:
            print("\nDemo stopped.")
    else:
        stream_from_serial(args.port, args.baud)

if __name__ == "__main__":
    main()
