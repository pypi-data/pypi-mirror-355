# sha256.py

"""
SHA-256 Hash Function Implementation (Skeleton)

This module implements the SHA-256 cryptographic hash function.
You will fill in the actual algorithm steps.
"""

# Constants (first 32 bits of the fractional parts of the cube roots of the first 64 primes)
K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]
h = [
    0x6a09e667,
    0xbb67ae85,
    0x3c6ef372,
    0xa54ff53a,
    0x510e527f,
    0x9b05688c,
    0x1f83d9ab,
    0x5be0cd19
]
def right_rotate(value, bits):
    """
    Right rotate a 32-bit integer value by a given number of bits.
    """
    # Implement bit rotation
    return ((value >> bits) | (value << (32 - bits))) & 0xFFFFFFFF

def sha256_pad(message_bytes):
    """
    Pad the input message_bytes according to SHA-256 specification.
    Returns the padded byte array.
    """
    message_length_bits = len(message_bytes) * 8
    
    # Step 1: Append the '1' bit as 0x80 (10000000 in binary)
    padded = message_bytes + b'\x80'
    
    # Step 2: Calculate how many zero bytes to append
    # Total length must be congruent to 448 bits (56 bytes) mod 512 bits (64 bytes)
    # So the padded message length before length field must be a multiple of 64 bytes minus 8 bytes (length field)
    padding_length = (56 - (len(padded) % 64)) % 64
    
    # Step 3: Append zero bytes
    padded += b'\x00' * padding_length
    
    # Step 4: Append original length as 8-byte big-endian integer
    padded += message_length_bits.to_bytes(8, byteorder='big')
    
    return padded

def sha256_parse_blocks(padded_message):
    """
    Parse the padded message into 512-bit (64-byte) blocks.
    Returns a list of byte blocks.
    """
    blocks = []
    for i in range(0, len(padded_message), 64):
        blocks.append(padded_message[i:i+64])
    return blocks

def sha256_compress(block, h):
    """
    Perform the SHA-256 compression function on a single 512-bit block.

    Parameters:
    - block: bytes, 64 bytes representing one block
    - h: list of 8 integers, current hash state

    Returns:
    - list of 8 integers, updated hash state
    """

    # Prepare the message schedule W
    W = [0] * 64
    for t in range(16):
        W[t] = int.from_bytes(block[t*4:(t*4)+4], 'big')

    for t in range(16, 64):
        s0 = (right_rotate(W[t-15], 7) ^
              right_rotate(W[t-15], 18) ^
              (W[t-15] >> 3))
        s1 = (right_rotate(W[t-2], 17) ^
              right_rotate(W[t-2], 19) ^
              (W[t-2] >> 10))
        W[t] = (W[t-16] + s0 + W[t-7] + s1) & 0xFFFFFFFF

    # Initialize working variables with current hash state
    a, b, c, d, e, f, g, hh = h

    # Main compression loop
    for t in range(64):
        S1 = (right_rotate(e, 6) ^
              right_rotate(e, 11) ^
              right_rotate(e, 25))
        ch = (e & f) ^ ((~e) & g)
        temp1 = (hh + S1 + ch + K[t] + W[t]) & 0xFFFFFFFF
        S0 = (right_rotate(a, 2) ^
              right_rotate(a, 13) ^
              right_rotate(a, 22))
        maj = (a & b) ^ (a & c) ^ (b & c)
        temp2 = (S0 + maj) & 0xFFFFFFFF

        hh = g
        g = f
        f = e
        e = (d + temp1) & 0xFFFFFFFF
        d = c
        c = b
        b = a
        a = (temp1 + temp2) & 0xFFFFFFFF

    # Compute the new hash state by adding the compressed chunk
    h[0] = (h[0] + a) & 0xFFFFFFFF
    h[1] = (h[1] + b) & 0xFFFFFFFF
    h[2] = (h[2] + c) & 0xFFFFFFFF
    h[3] = (h[3] + d) & 0xFFFFFFFF
    h[4] = (h[4] + e) & 0xFFFFFFFF
    h[5] = (h[5] + f) & 0xFFFFFFFF
    h[6] = (h[6] + g) & 0xFFFFFFFF
    h[7] = (h[7] + hh) & 0xFFFFFFFF

    return h


def sha256(message):
    """
    Compute the SHA-256 hash of the input message (string or bytes).

    Parameters:
    - message: str or bytes

    Returns:
    - hex string of the digest (64 hex characters)
    """
    # 1. Convert input to bytes if it's a string
    if isinstance(message, str):
        message = message.encode('utf-8')
    
    # 2. Pad the message bytes
    padded_message = sha256_pad(message)
    
    # 3. Parse the padded message into 64-byte blocks
    blocks = sha256_parse_blocks(padded_message)
    
    # 4. Initialize hash values (copy so original h is untouched)
    h_values = h.copy()
    
    # 5. Process each block with the compression function
    for block in blocks:
        h_values = sha256_compress(block, h_values)
    
    # 6. Produce the final digest by concatenating the 8 hash values
    # Convert each to 8 hex digits (32 bits), join into a 64-character string
    digest = ''.join(f'{value:08x}' for value in h_values)
    return digest

if __name__ == "__main__":
    test_message = "nigger"
    digest = sha256(test_message)
    print(f"SHA-256('{test_message}') = {digest}")