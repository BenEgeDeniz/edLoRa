import struct
from enum import IntEnum

class MsgType(IntEnum):
    HEARTBEAT = 0x00
    GPS = 0x01
    ALTIMETER = 0x02
    IMU = 0x03
    COMMAND = 0x04
    SYS_STATE = 0x05   # E.g., Battery level, temperature, flight phase
    ORIENTATION = 0x06 # Quaternions or Euler angles
    EVENT = 0x07       # Flight events (Launch, Apogee, Deployments)
    ACK = 0xFD         # Command Acknowledgement (payload = original seq_num)
    ERROR_MSG = 0xFE   # Error/Fault conditions
    CUSTOM = 0xFF

class Packet:
    SYNC_BYTE = 0xED
    BROADCAST_ID = 0xFF
    MAX_PAYLOAD_SIZE = 240
    HEADER_SIZE = 10  # Sync(1), Sender(1), Recv(1), Type(1), Seq(1), Time(4), Len(1)
    FOOTER_SIZE = 2 # CRC16

    def __init__(self, sender_id: int = 0, receiver_id: int = 0, msg_type: MsgType = MsgType.CUSTOM, seq_num: int = 0, timestamp: int = 0, payload: bytes = b""):
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.msg_type = msg_type
        self.seq_num = seq_num
        self.timestamp = timestamp
        self.payload = payload

    @property
    def payload_len(self) -> int:
        return len(self.payload)

    def is_targeted_to(self, my_id: int) -> bool:
        """Check if the packet is targeted to my_id, or is a broadcast"""
        return self.receiver_id == my_id or self.receiver_id == self.BROADCAST_ID

    def create_ack(self, my_id: int, current_timestamp: int) -> "Packet":
        """Generate an ACK packet targeted back to the sender of this packet."""
        ack_p = Packet(
            sender_id=my_id,
            receiver_id=self.sender_id, # Target the original sender
            msg_type=MsgType.ACK,
            seq_num=0, # ACKs don't strictly need their own sequences, but could use one.
            timestamp=current_timestamp,
            payload=bytes([self.seq_num]) # Payload is exactly 1 byte: the original sequence number
        )
        return ack_p

    def set_payload_string(self, text: str):
        """Helper to encode a string directly to the payload bytes"""
        self.payload = text.encode('utf-8')[:self.MAX_PAYLOAD_SIZE]

    def get_payload_string(self) -> str:
        """Helper to decode payload bytes back to a string"""
        return self.payload.decode('utf-8', errors='replace')

    def pack(self) -> bytes:
        if len(self.payload) > self.MAX_PAYLOAD_SIZE:
            raise ValueError(f"Payload too large. Max: {self.MAX_PAYLOAD_SIZE}")
        if not (0 <= self.sender_id <= 255):
            raise ValueError("Sender ID must be between 0 and 255")
        if not (0 <= self.receiver_id <= 255):
            raise ValueError("Receiver ID must be between 0 and 255")
        if not (0 <= self.seq_num <= 255):
            raise ValueError("Sequence number must be between 0 and 255")
        if self.timestamp < 0 or self.timestamp > 0xFFFFFFFF:
            raise ValueError("Timestamp must be a 32-bit unsigned integer")


        # Pack header
        # Format: B(sync), B(sender), B(recv), B(type), B(seq), I(time, 4bytes), B(len)
        header = struct.pack("<BBBBBIB", 
            self.SYNC_BYTE,
            self.sender_id,
            self.receiver_id,
            int(self.msg_type),
            self.seq_num,
            self.timestamp,
            self.payload_len
        )

        # Body = Header + Payload
        body = header + self.payload

        # Calculate CRC
        crc = self.calculate_crc(body)
        
        # Append CRC (Little Endian)
        footer = struct.pack("<H", crc)
        
        return body + footer

    @classmethod
    def unpack(cls, buffer: bytes) -> "Packet":
        if len(buffer) < cls.HEADER_SIZE + cls.FOOTER_SIZE:
            raise ValueError("Buffer too short")

        sync, sender, receiver, msg_type_val, seq, timestamp, payload_len = struct.unpack("<BBBBBIB", buffer[:cls.HEADER_SIZE])

        if sync != cls.SYNC_BYTE:
            raise ValueError(f"Invalid sync byte. Expected {cls.SYNC_BYTE}, got {sync}")

        if len(buffer) < cls.HEADER_SIZE + payload_len + cls.FOOTER_SIZE:
            raise ValueError("Buffer shorter than payload length specified")

        # Verify CRC
        expected_body = buffer[:cls.HEADER_SIZE + payload_len]
        received_crc = struct.unpack("<H", buffer[cls.HEADER_SIZE + payload_len:cls.HEADER_SIZE + payload_len + 2])[0]
        calculated_crc = cls.calculate_crc(expected_body)

        if received_crc != calculated_crc:
            raise ValueError(f"CRC Mismatch. Expected {calculated_crc}, got {received_crc}")

        payload = buffer[cls.HEADER_SIZE:cls.HEADER_SIZE + payload_len]

        return cls(
            sender_id=sender,
            receiver_id=receiver,
            msg_type=MsgType(msg_type_val),
            seq_num=seq,
            timestamp=timestamp,
            payload=payload
        )

    @staticmethod
    def calculate_crc(data: bytes) -> int:
        """Calculate CRC-16 CCITT (0x1021 polynomial, initial 0xFFFF)"""
        crc = 0xFFFF
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc <<= 1
                crc &= 0xFFFF # Keep it 16-bit
        return crc
