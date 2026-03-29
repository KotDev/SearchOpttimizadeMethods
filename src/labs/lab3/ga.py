import numpy as np


class GeneticAlgorithm:
    def __init__(self, func, bounds, pop_size=50, mut_rate=0.1, cross_rate=0.8):
        self.func = func
        self.bounds = np.array(bounds)
        self.pop_size = pop_size
        self.mut_rate = mut_rate
        self.cross_rate = cross_rate
        self.history = []  # Список поколений (каждое поколение - массив точек)

    def selection(self, pop, fitness):
        """Турнирная селекция"""
        idx = np.random.choice(len(pop), 3)
        best_idx = idx[np.argmin(fitness[idx])]
        return pop[best_idx].copy()

    def crossover(self, p1, p2):
        """Арифметическое скрещивание"""
        if np.random.rand() < self.cross_rate:
            alpha = np.random.rand()
            c1 = alpha * p1 + (1 - alpha) * p2
            c2 = alpha * p2 + (1 - alpha) * p1
            return c1, c2
        return p1.copy(), p2.copy()

    def mutate(self, ind):
        """Мутация: случайное смещение в пределах 10% от диапазона"""
        if np.random.rand() < self.mut_rate:
            scale = (self.bounds[:, 1] - self.bounds[:, 0]) * 0.1
            ind += np.random.normal(0, scale, size=ind.shape)
            ind = np.clip(ind, self.bounds[:, 0], self.bounds[:, 1])
        return ind

    def solve(self, generations=50):
        self.history = []
        # Инициализация
        pop = np.random.uniform(self.bounds[:, 0], self.bounds[:, 1], (self.pop_size, 2))

        for g in range(generations):
            # Сохраняем текущее «облако» для визуализации
            self.history.append(pop.copy())

            fitness = np.array([self.func(p) for p in pop])
            new_pop = []

            while len(new_pop) < self.pop_size:
                parent1 = self.selection(pop, fitness)
                parent2 = self.selection(pop, fitness)

                child1, child2 = self.crossover(parent1, parent2)

                new_pop.append(self.mutate(child1))
                if len(new_pop) < self.pop_size:
                    new_pop.append(self.mutate(child2))

            pop = np.array(new_pop)

        return self.history