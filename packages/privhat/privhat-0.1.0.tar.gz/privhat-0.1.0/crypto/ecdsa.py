from sha256 import sha256
from utils import modinv
import secrets
from ecc import EllipticCurve 

class ECDSA:
    def __init__(self, curve_params):
        self.p = curve_params['p']
        self.a = curve_params['a']
        self.b = curve_params['b']
        self.G = curve_params['G']
        self.n = curve_params['n']
        self.curve = EllipticCurve(self.a, self.b, self.p)

    def generate_keypair(self):
        # Generate a private key (random integer in [1, n-1])
        # Compute the public key as the scalar multiplication of the base point G by the private key
        private_key = secrets.randbelow(self.n - 1) + 1  
        public_key = self.curve.scalar_mult(private_key, self.G)
        return private_key, public_key

    def sign(self, message, private_key):
        if isinstance(message, str):
            message = message.encode()

        e = int(sha256(message), 16)

        while True:
            k = secrets.randbelow(self.n - 1) + 1
            x, _ = self.curve.scalar_mult(k, self.G)
            r = x % self.n
            if r == 0:
                continue

            try:
                k_inv = modinv(k, self.n)
            except Exception:
                continue

            s = (k_inv * (e + r * private_key)) % self.n
            if s == 0:
                continue

            return (r, s)


    def verify(self, message, signature, public_key):
        if isinstance(message, str):
            message = message.encode()

        r, s = signature
        if not (1 <= r < self.n) or not (1 <= s < self.n):
            return False

        e = int(sha256(message), 16)
        try:
            s_inv = modinv(s, self.n)
        except Exception:
            return False

        u1 = (e * s_inv) % self.n
        u2 = (r * s_inv) % self.n

        point = self.curve.point_add(
            self.curve.scalar_mult(u1, self.G),
            self.curve.scalar_mult(u2, public_key)
        )

        if point is None:
            return False

        x, _ = point
        return (r % self.n) == (x % self.n)


if __name__ == "__main__":
    # Example curve parameters (secp192k1-like small example, just for testing)
    curve_params = {
        'p': 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFEE37,
        'a': 0,
        'b': 3,
        'G': (
            0xDB4FF10EC057E9AE26B07D0280B7F4341DA5D1B1EAE06C7D,
            0x9B2F2F6D9C5628A7844163D015BE86344082AA88D95E2F9D
        ),
        'n': 0xFFFFFFFFFFFFFFFFFFFFFFFE26F2FC170F69466A74DEFD8D,
    }

    ecdsa = ECDSA(curve_params)

    # Generate keys
    private_key, public_key = ecdsa.generate_keypair()
    print(f"Private Key: {private_key}")
    print(f"Public Key: {public_key}")

    message = "BABYLON WAGES WAR ON BABYLON"
    print(f"Message: {message}")

    # Sign the message
    signature = ecdsa.sign(message, private_key)
    print(f"Signature: {signature}")

    # Verify the signature
    valid = ecdsa.verify(message, signature, public_key)
    print(f"Signature valid? {valid}")

    # Test invalid signature (tamper with signature)
    bad_signature = (signature[0], (signature[1] + 1) % curve_params['n'])
    invalid = ecdsa.verify(message, bad_signature, public_key)
    print(f"Tampered Signature valid? {invalid}")
