# diffie_hellman.py
from utils import is_prime, modexp
import random
import secrets

# Finding p and g, not feasible
def generate_large_prime(bits=512):
    while True:
        candidate = random.getrandbits(bits)
        candidate |= (1 << bits - 1) | 1  
        if is_prime(candidate):
            return candidate
        
def find_primitive_root(p):
    phi = p - 1
    factors = set()
    n = phi

    i = 2
    while i * i <= n:
        if n % i == 0:
            factors.add(i)
            while n % i == 0:
                n //= i
        i += 1
    if n > 1:
        factors.add(n)

    for g in range(2, p):
        flag = True
        for q in factors:
            if modexp(g, phi // q, p) == 1:
                flag = False
                break
        if flag:
            return g

    return None

# Step 1: Define global parameters
# - Prime number (p)
# - Primitive root modulo p (g)
def define_global_parameters(bits=512):
    p = generate_large_prime(bits)
    g = find_primitive_root(p)
    return p, g

# Step 2: Generate private key for a user
def generate_private_key(p):
    # Choose private key a in [2, p-2]
    return secrets.randbelow(p - 3) + 2

# Step 3: Compute public key
def compute_public_key(private_key, g, p):
    return modexp(g, private_key, p)

# Step 4: Compute shared secret
def compute_shared_secret(their_public_key, own_private_key, p):
    return modexp(their_public_key, own_private_key, p)

# Standard 2048-bit MODP Group (RFC 3526) prime and generator
p_2048 = int("""
FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E08
8A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431
B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42
E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1
FE649286651ECE65381FFFFFFFFFFFFFFFF
""".replace('\n', '').replace(' ', ''), 16)

g_2048 = 2

# Optional Step: Simulate key exchange between Alice and Bob
def simulate_key_exchange(use_standard_params=False):
    if use_standard_params:
        p, g = p_2048, g_2048
    else:
        p, g = define_global_parameters(bits=512)
        
    print(f"Global parameters:\np = {p}\ng = {g}\n")

    alice_private = generate_private_key(p)
    alice_public = compute_public_key(alice_private, g, p)
    print(f"Alice's private key: {alice_private}")
    print(f"Alice's public key: {alice_public}\n")

    bob_private = generate_private_key(p)
    bob_public = compute_public_key(bob_private, g, p)
    print(f"Bob's private key: {bob_private}")
    print(f"Bob's public key: {bob_public}\n")

    alice_shared_secret = compute_shared_secret(bob_public, alice_private, p)
    bob_shared_secret = compute_shared_secret(alice_public, bob_private, p)
    
    print(f"Alice's computed shared secret: {alice_shared_secret}")
    print(f"Bob's computed shared secret: {bob_shared_secret}\n")

    if alice_shared_secret == bob_shared_secret:
        print("Success! Shared secrets match.")
    else:
        print("Error! Shared secrets do NOT match.")

if __name__ == "__main__":
    simulate_key_exchange(use_standard_params=True)
