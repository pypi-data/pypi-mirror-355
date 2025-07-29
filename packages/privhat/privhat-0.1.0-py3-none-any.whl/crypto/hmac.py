# h_mac.py
from sha256 import sha256

def h_mac(key, message, hash_function):
    # 1. Define block size for the hash function (e.g., 64 bytes for SHA-256)
    block_size = 64  
    
    # 2. If key length > block size, hash the key
    if len(key) > block_size:
        key = bytes.fromhex(sha256(key))
    
    # 3. If key length < block size, pad the key with zeros to block size
    if len(key) < block_size:
        key = key + b'\x00' * (block_size - len(key))

    # 4. Create inner padding by XOR-ing the key with 0x36 repeated to block size
    ipad = bytes([b ^ 0x36 for b in key])

    # 5. Create outer padding by XOR-ing the key with 0x5c repeated to block size
    opad = bytes([b ^ 0x5c for b in key])

    # 6. Compute inner hash: hash_function(inner_padding + message)
    inner_hash = bytes.fromhex(sha256(ipad + message))

    # 7. Compute outer hash: hash_function(outer_padding + inner_hash)
    outer_hash = hash_function(opad + inner_hash)

    # 8. Return the final HMAC value (hex string is fine since your hash_function returns hex string)
    return outer_hash

def verify_hmac(key, message, received_hmac, hash_function):
    computed_hmac = h_mac(key, message, hash_function)
    return computed_hmac == received_hmac

if __name__ == "__main__":
    key = b"mysecretkey"
    message = b"hello world"
    hmac_value = h_mac(key, message, sha256)
    print("HMAC:", hmac_value)
    is_valid = verify_hmac(key, message, hmac_value, sha256)
    print("Verification result:", is_valid)  # Should print True
