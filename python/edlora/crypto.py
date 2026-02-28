from typing import List
from . import Packet

class XorCipher:
    """
    Extremely lightweight XOR Cipher for payload obfuscation.
    Can be replaced with AES libraries if strict security is needed.
    """
    def __init__(self, key: int = 0xAA):
        self.key = key & 0xFF
        
    def set_key(self, new_key: int):
        self.key = new_key & 0xFF

    def process(self, packet: Packet) -> Packet:
        """Encrypts/Decrypts the payload in-place"""
        obfuscated_payload = bytearray(packet.payload)
        for i in range(len(obfuscated_payload)):
            obfuscated_payload[i] ^= self.key
        packet.payload = bytes(obfuscated_payload)
        return packet
