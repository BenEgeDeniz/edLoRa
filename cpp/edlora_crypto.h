#ifndef EDLORA_CRYPTO_H
#define EDLORA_CRYPTO_H

#include "edlora.h"

namespace edlora {
namespace crypto {

// Extremely lightweight XOR Cipher for payload obfuscation.
// Can be replaced with AES-128/256 if strict security is needed.
class XorCipher {
private:
    uint8_t key;
public:
    XorCipher(uint8_t encryption_key = 0xAA) : key(encryption_key) {}
    
    void set_key(uint8_t new_key) { key = new_key; }

    // Encrypts/Decrypts the payload in-place
    void process(Packet& packet) {
        for (size_t i = 0; i < packet.payload_len; ++i) {
            packet.payload[i] ^= key;
        }
    }
};

} // namespace crypto
} // namespace edlora

#endif // EDLORA_CRYPTO_H
