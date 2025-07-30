import unittest
from pycast.ecc import EllipticCurve, KeyEntropyCalculator

class TestEllipticCurve(unittest.TestCase):
    def setUp(self):
        self.a = 56698187605326110043627228396178346077120614539475214109386828188763884139993
        self.b = 17577232497321838841075697789794520262950426058923084567046852300633325438902
        self.p = 76884956397045344220809746629001649093037950200943055203735601445031516197751
        self.Gx = 63243729749562333355292243550312970334778175571054726587095381623627144114786
        self.Gy = 38218615093753523893122277964030810387585405539772602581557831887485717997975
        self.n = 0xA9FB57DBA1EEA9BC3E660A909D838D718AFCED59
        self.curve = EllipticCurve(self.a, self.b, self.p, self.Gx, self.Gy, self.n)

    def test_point_on_curve(self):
        self.assertTrue(self.curve.is_point_on_curve(self.curve.G))

    def test_key_generation(self):
        priv = self.curve.generate_private_key()
        pub = self.curve.public_key_from_private(priv)
        self.assertTrue(self.curve.is_point_on_curve(pub))

    def test_entropy_calculation(self):
        calc = KeyEntropyCalculator(self.curve)
        key, entropy = calc.generate_high_entropy_key(num_trials=10)
        self.assertIsInstance(key, int)
        self.assertGreater(entropy, 0)

if __name__ == '__main__':
    unittest.main()
