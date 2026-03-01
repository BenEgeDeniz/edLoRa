import unittest
import struct
from edlora import Packet, MsgType
from edlora.crypto import XorCipher

class TestEdLoraProtocol(unittest.TestCase):
    def test_basic_packing(self):
        p = Packet(sender_id=0x10, receiver_id=0x20, msg_type=MsgType.HEARTBEAT, seq_num=5)
        packed = p.pack()
        self.assertEqual(len(packed), 8) # 6 header + 0 payload + 2 CRC
        self.assertEqual(packed[0], Packet.SYNC_BYTE)

    def test_string_payload(self):
        p = Packet()
        p.set_payload_string("TEST")
        self.assertEqual(p.payload_len, 4)
        
        packed = p.pack()
        rx_p = Packet.unpack(packed)
        self.assertEqual(rx_p.get_payload_string(), "TEST")

    def test_payload_too_large(self):
        p = Packet()
        p.payload = b'A' * 250
        with self.assertRaises(ValueError):
            p.pack()

    def test_crc_failure(self):
        p = Packet(payload=b"VALID")
        packed = bytearray(p.pack())
        packed[6] = 0xFF # Corrupt a byte in the payload
        with self.assertRaises(ValueError) as context:
            Packet.unpack(bytes(packed))
        self.assertTrue("CRC" in str(context.exception))

    def test_invalid_sync_byte(self):
        p = Packet()
        packed = bytearray(p.pack())
        packed[0] = 0x00 # Invalid sync byte
        with self.assertRaises(ValueError):
            Packet.unpack(bytes(packed))

    def test_crypto_wrapper(self):
        original = Packet(payload=b"SECRET")
        cipher = XorCipher(0xAB)
        
        # Encrypt
        encrypted = cipher.process(original)
        self.assertNotEqual(encrypted.payload, b"SECRET")
        
        # Test serialization of encrypted
        packed = encrypted.pack()
        
        # Decrypt
        rx = Packet.unpack(packed)
        decrypted = cipher.process(rx)
        
        self.assertEqual(decrypted.payload, b"SECRET")

    def test_stream_fragmentation(self):
        # Simulate: HALFPACKET + FULLPACKET + HALFPACKET
        p = Packet(sender_id=0xAA, msg_type=MsgType.COMMAND)
        p.set_payload_string("FULL")
        valid_packet_bytes = p.pack()
        
        # Craft a stream with garbage/partial packets on both ends
        half_packet_before = valid_packet_bytes[:4]
        half_packet_after = valid_packet_bytes[:5]
        stream = half_packet_before + valid_packet_bytes + half_packet_after
        
        # Stream parser scanning logic
        recovered = None
        for i in range(len(stream)):
            if stream[i] == Packet.SYNC_BYTE:
                try:
                    # Try unpacking from this sync byte onwards
                    rx = Packet.unpack(stream[i:])
                    recovered = rx
                    break
                except ValueError:
                    pass # Keep scanning
        
        self.assertIsNotNone(recovered)
        self.assertEqual(recovered.get_payload_string(), "FULL")

if __name__ == '__main__':
    unittest.main()
