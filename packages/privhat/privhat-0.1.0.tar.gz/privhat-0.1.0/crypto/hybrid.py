from dh import generate_private_key, compute_public_key, compute_shared_secret, p_2048, g_2048
from aes import AES, pkcs7_pad, pkcs7_unpad, BLOCK_SIZE
from sha256 import sha256

def derive_aes_key(shared_secret_int, key_length=16):
    secret_bytes = shared_secret_int.to_bytes((shared_secret_int.bit_length() + 7) // 8, 'big')
    hash_hex = sha256(secret_bytes)
    hash_bytes = bytes.fromhex(hash_hex)
    return hash_bytes[:key_length]

def main():
    alice_private = generate_private_key(p_2048)
    alice_public = compute_public_key(alice_private, g_2048, p_2048)

    bob_private = generate_private_key(p_2048)
    bob_public = compute_public_key(bob_private, g_2048, p_2048)

    alice_shared = compute_shared_secret(bob_public, alice_private, p_2048)
    bob_shared = compute_shared_secret(alice_public, bob_private, p_2048)

    assert alice_shared == bob_shared, "Shared secrets don't match!"
    shared_secret = alice_shared

    key = derive_aes_key(shared_secret)

    aes = AES(key)

    plaintext = input("Enter the message to encrypt: ").encode('utf-8')
    padded_plaintext = pkcs7_pad(plaintext, BLOCK_SIZE)

    encrypted = b''
    for i in range(0, len(padded_plaintext), BLOCK_SIZE):
        block = padded_plaintext[i:i+BLOCK_SIZE]
        encrypted += aes.encrypt_block(block)

    print("Ciphertext (hex):", encrypted.hex())

    decrypted = b''
    for i in range(0, len(encrypted), BLOCK_SIZE):
        block = encrypted[i:i+BLOCK_SIZE]
        decrypted += aes.decrypt_block(block)

    decrypted_plaintext = pkcs7_unpad(decrypted)
    print("Decrypted:", decrypted_plaintext.decode())

if __name__ == "__main__":
    main()
