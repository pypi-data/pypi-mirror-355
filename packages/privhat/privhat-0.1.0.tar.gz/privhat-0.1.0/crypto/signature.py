# rsa_signature.py

from crypto.rsa import encrypt, decrypt, generate_keypair
from crypto.sha256 import sha256

def sign(message_text, private_key):
    """
    Sign the input message string with the RSA private key.
    Steps:
    - Hash the message (SHA-256)
    - Convert hash digest to integer
    - Use RSA decrypt (private key operation) on the hash integer to create signature
    - Return the signature integer
    """
    hashed = sha256(message_text)
    hashed_int = int(hashed, 16)
    signature = decrypt(hashed_int, private_key)
    return signature

def verify(message_text, signature, public_key):
    """
    Verify the RSA signature on the message.
    Steps:
    - Hash the message (SHA-256)
    - Convert hash digest to integer
    - Use RSA encrypt (public key operation) on the signature integer
    - Compare the decrypted signature integer to the message hash integer
    - Return True if valid, False otherwise
    """
    hashed = sha256(message_text)
    hashed_int = int(hashed, 16)
    recovered_hash_int = encrypt(signature, public_key)
    return recovered_hash_int == hashed_int
    