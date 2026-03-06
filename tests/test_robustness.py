import unittest
import struct
from edlora import Packet, MsgType

class TestRobustness(unittest.TestCase):
    def test_pack_type_assertions(self):
        # Test invalid sender ID
        p = Packet(sender_id=256)
        with self.assertRaises(ValueError):
            p.pack()
            
        # Test invalid receiver ID
        p = Packet(receiver_id=-1)
        with self.assertRaises(ValueError):
            p.pack()

    def test_unpack_malformed_buffer(self):
        # Truncated buffer
        with self.assertRaises(ValueError):
            Packet.unpack(b"1234")
            
        # Invalid sync byte
        bad_sync = b"\x00" * 20
        with self.assertRaises(ValueError):
            Packet.unpack(bad_sync)

    def test_unpack_fuzzed_crc(self):
        valid_packet = Packet(sender_id=1, receiver_id=2, msg_type=MsgType.HEARTBEAT).pack()
        
        # Flip a bit in the CRC (last 2 bytes)
        fuzzed = bytearray(valid_packet)
        fuzzed[-1] ^= 0xFF
        
        with self.assertRaises(ValueError):
            Packet.unpack(bytes(fuzzed))

    def test_unpack_fuzzed_payload(self):
        valid_packet = Packet(sender_id=1, receiver_id=2, msg_type=MsgType.HEARTBEAT, payload=b"test").pack()
        
        # Flip a bit in the payload
        fuzzed = bytearray(valid_packet)
        fuzzed[12] ^= 0xFF
        
        with self.assertRaises(ValueError):
            Packet.unpack(bytes(fuzzed))

if __name__ == '__main__':
    unittest.main()
