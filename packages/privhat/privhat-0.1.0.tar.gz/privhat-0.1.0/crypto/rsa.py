# rsa.py
import random
from utils import gcd, is_prime, modexp, modinv, int_to_text, text_to_int
def generate_keypair(bit_length):
    def generate_prime_candidate(bits):
        return random.getrandbits(bits) | (1 << (bits - 1)) | 1  
    def find_prime(bits):
        candidate = generate_prime_candidate(bits)
        while not is_prime(candidate):
            candidate = generate_prime_candidate(bits)
        return candidate
    p = find_prime(bit_length)
    q = find_prime(bit_length)
    while q == p:
        q = find_prime(bit_length)
    n = p * q
    phi_n = (p-1) * (q-1)
    e = 65537
    while gcd(e, phi_n) != 1:
        e = random.randrange(3, phi_n, 2)
    d = modinv(e, phi_n)
    return ((e, n), (d, n))

def encrypt(message, public_key):
    e, n = public_key
    c = modexp(message, e, n)
    return c

def decrypt(ciphertext, private_key):
    d, n = private_key
    m = modexp(ciphertext, d, n)
    return m

