import random
import numpy as np

class DynamicAESSBoxGA:
    def __init__(self, population_size=50, generations=1, mutation_rate=0.1):
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate

    def generate_sbox(self):
        return np.random.permutation(256).tolist()

    def evaluate_sbox(self, sbox):
        return self.compute_non_linearity(sbox) + self.compute_avalanche(sbox)

    def compute_non_linearity(self, sbox):
        table = np.zeros((256, 256), dtype=int)
        for x in range(256):
            for y in range(256):
                table[x ^ y][sbox[x] ^ sbox[y]] += 1
        return np.sum(table == 0)

    def compute_avalanche(self, sbox):
        flips = 0
        for x in range(256):
            for bit in range(8):
                fx = x ^ (1 << bit)
                if sbox[x] != sbox[fx]:
                    flips += 1
        return flips / (256 * 8)

    def crossover(self, p1, p2):
        cut = random.randint(1, 255)
        child = np.concatenate((p1[:cut], p2[cut:]))
        return self.repair_sbox(child)

    def mutate(self, sbox):
        if random.random() < self.mutation_rate:
            i, j = random.sample(range(256), 2)
            sbox[i], sbox[j] = sbox[j], sbox[i]
        return sbox

    def repair_sbox(self, sbox):
        missing = set(range(256)) - set(sbox)
        duplicates = {x for x in sbox if list(sbox).count(x) > 1}
        fixed = list(sbox)
        for i, val in enumerate(sbox):
            if val in duplicates:
                fixed[i] = missing.pop()
                duplicates.remove(val)
        return fixed

    def apply_ga(self):
        pop = [self.generate_sbox() for _ in range(self.population_size)]
        for _ in range(self.generations):
            scores = [self.evaluate_sbox(sbox) for sbox in pop]
            ranked = sorted(zip(scores, pop), reverse=True)
            best = ranked[0][1]
            survivors = [sbox for _, sbox in ranked[:self.population_size // 2]]
            next_gen = []
            for _ in range(self.population_size // 2):
                p1, p2 = random.sample(survivors, 2)
                child = self.crossover(p1, p2)
                next_gen.append(self.mutate(child))
            pop = survivors + next_gen
        return best
