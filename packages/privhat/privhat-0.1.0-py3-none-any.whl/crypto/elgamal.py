from dh import (
    define_global_parameters,
    generate_private_key,
    compute_public_key,
)

from utils import (
    modexp,
    text_to_int, 
    int_to_text
)

import secrets

class ElGamal:
    def __init__(self, use_standard_params=True, bits=512):
        # Step 1: Initialize domain parameters
        if use_standard_params:
            # Standard 2048-bit MODP Group from RFC 3526
            self.p = int("""
            FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E08
            8A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431
            B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42
            E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1
            FE649286651ECE65381FFFFFFFFFFFFFFFF
            """.replace('\n', '').replace(' ', ''), 16)
            self.g = 2
        else:
            # Use your own random prime and primitive root
            self.p, self.g = define_global_parameters(bits)

    def key_generation(self):
            # Step 2: Generate private key x
            private_key = generate_private_key(self.p)
            
            # Step 3: Compute public key y = g^x mod p
            public_key = compute_public_key(private_key, self.g, self.p)
            
            # Return (public_key, private_key)
            return public_key, private_key


    def encrypt(self, message, public_key):
        # If input is string, convert to int
        if isinstance(message, str):
            m_int = text_to_int(message)
        elif isinstance(message, int):
            m_int = message
        else:
            raise TypeError("Message must be a string or an integer")

        if not (0 < m_int < self.p):
            raise ValueError("Message integer out of range for encryption")

        k = secrets.randbelow(self.p - 2) + 1
        c1 = modexp(self.g, k, self.p)
        s = modexp(public_key, k, self.p)
        c2 = (m_int * s) % self.p

        return (c1, c2)

    def decrypt(self, ciphertext, private_key):
        c1, c2 = ciphertext

        s = modexp(c1, private_key, self.p)
        s_inv = pow(s, -1, self.p)
        m_int = (c2 * s_inv) % self.p

        # Convert integer back to string
        message = int_to_text(m_int)
        return message

if __name__ == "__main__":
    elgamal = ElGamal(use_standard_params=True)
    pub, priv = elgamal.key_generation()

    original_msg = input()
    cipher = elgamal.encrypt(original_msg, pub)
    decrypted_msg = elgamal.decrypt(cipher, priv)

    print("Original:", original_msg)
    print("Decrypted:", decrypted_msg)
    assert decrypted_msg == original_msg