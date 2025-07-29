# ecc.py
from utils import modinv
import random
import secrets
# Step 1: Define the Elliptic Curve class
class EllipticCurve:
    def __init__(self, a, b, p):
        # Initialize curve parameters: y^2 = x^3 + ax + b over field mod p
        self.a = a
        self.b = b
        self.p = p
        self.O = None
        if (4 * a**3 + 27 * b**2) % p == 0:
            raise ValueError("The curve is singular (invalid).")


    def is_on_curve(self, point):
        if point is None:
            # Point at infinity is always on the curve
            return True

        x, y = point
        return (y * y) % self.p == (x ** 3 + self.a * x + self.b) % self.p

    def point_add(self, p1, p2):
        if p1 is None:
            return p2
        if p2 is None:
            return p1

        if p1 == p2:
            return self.point_double(p1)  # Delegate to point_double
        
        x1, y1 = p1
        x2, y2 = p2

        if x1 == x2 and y1 != y2:
            return None  # Point at infinity

        s = ((y2 - y1) * modinv(x2 - x1, self.p)) % self.p

        x3 = (s**2 - x1 - x2) % self.p
        y3 = (s * (x1 - x3) - y1) % self.p

        return (x3, y3)
    
    def point_double(self, p):
        if p is None:
            return None

        x, y = p
        s = ((3 * x**2 + self.a) * modinv(2 * y, self.p)) % self.p
        x3 = (s**2 - 2 * x) % self.p
        y3 = (s * (x - x3) - y) % self.p

        return (x3, y3)

    def scalar_mult(self, k, point):
        result = None  # Identity element (point at infinity)
        addend = point

        while k > 0:
            if k & 1:
                result = self.point_add(result, addend)
            addend = self.point_double(addend)
            k >>= 1  # Shift k right by 1 bit

        return result


# Step 2: Define utility functions (modular inverse, random scalar generator, etc.)


def generate_private_key(curve):
    # Generate a random scalar private key in [1, p-1]
    return secrets.randbelow(curve.p - 1) + 1

def generate_public_key(private_key, base_point, curve):
    # Compute public key Q = private_key * base_point on the curve
    return curve.scalar_mult(private_key, base_point)

# Step 3: Define ECC-based encryption (Elliptic Curve ElGamal or similar)
def encrypt(curve, base_point, public_key, message_point):
    r = secrets.randbelow(curve.p - 1) + 1
    C1 = curve.scalar_mult(r, base_point)     # rG
    rQ = curve.scalar_mult(r, public_key)     # rQ
    C2 = curve.point_add(message_point, rQ)   # M + rQ
    return (C1, C2)


def decrypt(curve, private_key, ciphertext):
    C1, C2 = ciphertext
    dC1 = curve.scalar_mult(private_key, C1)      # d * C1 = rQ
    # To subtract points, add inverse of dC1
    neg_dC1 = (dC1[0], (-dC1[1]) % curve.p)       # Inverse point on curve
    M = curve.point_add(C2, neg_dC1)               # M = C2 - dC1
    return M


# Step 4: Add example parameters and a sample test runner (optional)
def example_usage():
    # Example curve parameters (small values for illustration only!)
    a = 2
    b = 3
    p = 97  # prime modulus

    # Instantiate the elliptic curve
    curve = EllipticCurve(a, b, p)

    # Base point G on the curve (must be on the curve)
    G = (3, 6)

    # Generate private key (random scalar)
    private_key = generate_private_key(curve)
    print(f"Private Key: {private_key}")

    # Generate public key Q = d * G
    public_key = generate_public_key(private_key, G, curve)
    print(f"Public Key: {public_key}")

    # Message point M (must be a valid point on the curve)
    message_point = (3, 6)  # Changed here to a valid point on the curve
    if not curve.is_on_curve(message_point):
        raise ValueError("Message point is not on the curve!")

    print(f"Original Message Point: {message_point}")

    # Encrypt the message using the receiver's public key
    ciphertext = encrypt(curve, G, public_key, message_point)
    print(f"Ciphertext: {ciphertext}")

    # Decrypt the ciphertext using the private key
    decrypted_point = decrypt(curve, private_key, ciphertext)
    print(f"Decrypted Message Point: {decrypted_point}")

    # Check if decryption matches original message
    assert decrypted_point == message_point, "Decryption failed!"


if __name__ == "__main__":
    example_usage()

