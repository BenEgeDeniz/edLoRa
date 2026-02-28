from edlora import Packet, MsgType

def main():
    # 1. Create a packet matching the C++ test
    tx_packet = Packet(
        sender_id=0x10,
        receiver_id=0xFF,
        msg_type=MsgType.GPS,
        seq_num=1
    )
    tx_packet.set_payload_string("Hello LoRa!")

    # 2. Pack the packet
    packed_bytes = tx_packet.pack()
    
    print(f"Packed {len(packed_bytes)} bytes:")
    print(" ".join(f"{b:02x}" for b in packed_bytes))
    
    # 3. Target C++ byte sequence for verification
    target_bytes = bytes([0xed, 0x10, 0xff, 0x01, 0x01, 0x0b, 0x48, 0x65, 0x6c, 0x6c, 0x6f, 0x20, 0x4c, 0x6f, 0x52, 0x61, 0x21, 0x84, 0xcf])
    
    if packed_bytes == target_bytes:
        print("Success! Python packed bytes match C++ packed bytes perfectly.")
    else:
        print("Mismatch with C++ packed bytes!")
        print(f"Expected: {' '.join(f'{b:02x}' for b in target_bytes)}")
        
    print("-" * 30)
    
    # 4. Unpack the bytes
    try:
        rx_packet = Packet.unpack(packed_bytes)
        print("Unpacked successfully:")
        print(f"Sender: 0x{rx_packet.sender_id:02x}")
        print(f"Receiver: 0x{rx_packet.receiver_id:02x}")
        print(f"MsgType: {rx_packet.msg_type}")
        print(f"SeqNum: {rx_packet.seq_num}")
        print(f"Payload Len: {rx_packet.payload_len}")
        print(f"Payload (HEX): {' '.join(f'{b:02x}' for b in rx_packet.payload)}")
        print(f"Payload (STR): {rx_packet.get_payload_string()}")
    except Exception as e:
        print(f"Failed to unpack: {e}")

if __name__ == "__main__":
    main()
