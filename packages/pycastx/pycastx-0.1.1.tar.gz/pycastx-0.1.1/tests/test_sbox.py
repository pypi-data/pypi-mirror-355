import unittest
from pycast.sbox import DynamicAESSBoxGA

class TestDynamicAESSBoxGA(unittest.TestCase):
    def setUp(self):
        self.ga = DynamicAESSBoxGA(population_size=10, generations=2)

    def test_generate_sbox(self):
        sbox = self.ga.generate_sbox()
        self.assertEqual(len(set(sbox)), 256)

    def test_apply_ga(self):
        best_sbox = self.ga.apply_ga()
        self.assertEqual(len(set(best_sbox)), 256)

if __name__ == '__main__':
    unittest.main()
