import random
import math

class EllipticCurve:
    def __init__(self, a, b, p, Gx, Gy, n):
        self.a = a
        self.b = b
        self.p = p
        self.G = (Gx, Gy)
        self.n = n
        if not self.is_point_on_curve(self.G):
            raise ValueError("The base point G does not lie on the curve.")

    def point_addition(self, P, Q):
        if P is None: return Q
        if Q is None: return P
        if P == Q:
            if P[1] == 0: return None
            lam = (3 * P[0]**2 + self.a) * pow(2 * P[1], -1, self.p) % self.p
        else:
            if P[0] == Q[0]: return None
            lam = (Q[1] - P[1]) * pow(Q[0] - P[0], -1, self.p) % self.p
        x_r = (lam**2 - P[0] - Q[0]) % self.p
        y_r = (lam * (P[0] - x_r) - P[1]) % self.p
        return (x_r, y_r)

    def scalar_multiplication(self, k, P):
        result = None
        addend = P
        while k:
            if k & 1:
                result = addend if result is None else self.point_addition(result, addend)
            addend = self.point_addition(addend, addend)
            k >>= 1
        return result

    def generate_private_key(self):
        return random.getrandbits(256)

    def public_key_from_private(self, private_key):
        return self.scalar_multiplication(private_key, self.G)

    def is_point_on_curve(self, P):
        if P is None: return False
        x, y = P
        return (y**2 - (x**3 + self.a * x + self.b)) % self.p == 0

class KeyEntropyCalculator:
    def __init__(self, curve):
        self.curve = curve

    def shannon_entropy(self, data):
        if not data: return 0
        entropy = 0
        freq = {byte: data.count(byte) / len(data) for byte in set(data)}
        for p in freq.values():
            entropy -= p * math.log2(p)
        return entropy

    def private_key_to_byte_array(self, private_key):
        return [int(x) for x in bin(private_key)[2:].zfill(256)]

    def generate_high_entropy_key(self, num_trials=100):
        best_key, max_entropy = None, 0
        for _ in range(num_trials):
            key = self.curve.generate_private_key()
            entropy = self.shannon_entropy(self.private_key_to_byte_array(key))
            if entropy > max_entropy:
                best_key, max_entropy = key, entropy
        return best_key, max_entropy
