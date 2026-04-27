import numpy as np
from typing import Callable, List, Optional, Tuple


class ImmuneNetworkAlgorithm:
    """
    Иммунная сеть на основе клональной селекции для глобальной оптимизации.

    Поддерживает поитерационную визуализацию через callback.
    """

    def __init__(
        self,
        func: Callable,
        bounds: np.ndarray,
        population_size: int = 20,
        selected_count: int = 5,
        clone_factor: int = 6,
        mutation_scale: float = 0.15,
        suppression_radius: float = 0.2,
        newcomers_count: int = 4,
        max_iterations: int = 100,
        stagnation_limit: int = 20,
        verbose: bool = False,
    ):
        self.func = func
        self.bounds = np.array(bounds, dtype=float)
        self.dimension = len(bounds)

        self.population_size = population_size
        self.selected_count = selected_count
        self.clone_factor = clone_factor
        self.mutation_scale = mutation_scale
        self.suppression_radius = suppression_radius
        self.newcomers_count = newcomers_count
        self.max_iterations = max_iterations
        self.stagnation_limit = stagnation_limit
        self.verbose = verbose

        self.history: List[np.ndarray] = []
        self.best_history: List[float] = []
        self.best_positions_history: List[np.ndarray] = []

        self.best_position = None
        self.best_value = float("inf")

    def _random_position(self) -> np.ndarray:
        return np.random.uniform(self.bounds[:, 0], self.bounds[:, 1], size=self.dimension)

    def _evaluate(self, position: np.ndarray) -> float:
        return float(self.func(position))

    def _hypermutate(self, antibody: np.ndarray, score: float) -> np.ndarray:
        normalized_score = 1.0 / (1.0 + max(score, 0.0))
        scale = self.mutation_scale * (1.2 - normalized_score)
        delta = np.random.normal(0, scale, size=self.dimension) * (self.bounds[:, 1] - self.bounds[:, 0])
        mutated = antibody + delta
        return np.clip(mutated, self.bounds[:, 0], self.bounds[:, 1])

    def _suppress_population(self, population: List[np.ndarray], values: List[float]) -> Tuple[List[np.ndarray], List[float]]:
        if not population:
            return [], []

        order = np.argsort(values)
        survivors = []
        survivor_values = []

        for idx in order:
            candidate = population[idx]
            if not survivors:
                survivors.append(candidate.copy())
                survivor_values.append(values[idx])
                continue

            distances = [np.linalg.norm(candidate - survivor) for survivor in survivors]
            if min(distances) >= self.suppression_radius:
                survivors.append(candidate.copy())
                survivor_values.append(values[idx])

            if len(survivors) >= self.population_size:
                break

        return survivors, survivor_values

    def solve(self, real_time_callback: Optional[Callable] = None) -> Tuple[np.ndarray, float, List[np.ndarray]]:
        self.history = []
        self.best_history = []
        self.best_positions_history = []
        self.best_position = None
        self.best_value = float("inf")

        population = [self._random_position() for _ in range(self.population_size)]
        values = [self._evaluate(point) for point in population]

        stagnation_counter = 0
        last_best_value = float("inf")

        for iteration in range(self.max_iterations):
            ordered_indices = np.argsort(values)
            population = [population[i] for i in ordered_indices]
            values = [values[i] for i in ordered_indices]

            if values[0] < self.best_value:
                self.best_value = values[0]
                self.best_position = population[0].copy()

            current_population = np.array(population)
            self.history.append(current_population.copy())
            self.best_history.append(self.best_value)
            self.best_positions_history.append(self.best_position.copy() if self.best_position is not None else None)

            if real_time_callback is not None:
                should_continue = real_time_callback(
                    iteration, current_population, self.best_position, self.best_value
                )
                if should_continue is False:
                    break

            if self.verbose and iteration % 10 == 0:
                print(f"Итерация {iteration}: лучшее значение = {self.best_value:.10f}")

            selected_count = min(self.selected_count, len(population))
            selected = population[:selected_count]
            selected_values = values[:selected_count]

            clone_population = []
            clone_values = []

            for antibody, value in zip(selected, selected_values):
                clone_population.append(antibody.copy())
                clone_values.append(value)

                for _ in range(self.clone_factor):
                    clone = self._hypermutate(antibody, value)
                    clone_value = self._evaluate(clone)
                    clone_population.append(clone)
                    clone_values.append(clone_value)

                    if clone_value < self.best_value:
                        self.best_value = clone_value
                        self.best_position = clone.copy()

            survivors, survivor_values = self._suppress_population(clone_population, clone_values)

            while len(survivors) < max(self.population_size - self.newcomers_count, 1):
                point = self._random_position()
                point_value = self._evaluate(point)
                survivors.append(point)
                survivor_values.append(point_value)
                if point_value < self.best_value:
                    self.best_value = point_value
                    self.best_position = point.copy()

            newcomers = [self._random_position() for _ in range(self.newcomers_count)]
            newcomer_values = [self._evaluate(point) for point in newcomers]

            for point, point_value in zip(newcomers, newcomer_values):
                if point_value < self.best_value:
                    self.best_value = point_value
                    self.best_position = point.copy()

            population = survivors + newcomers
            values = survivor_values + newcomer_values

            if len(population) > self.population_size:
                order = np.argsort(values)[:self.population_size]
                population = [population[i] for i in order]
                values = [values[i] for i in order]

            if self.best_value < last_best_value:
                stagnation_counter = 0
                last_best_value = self.best_value
            else:
                stagnation_counter += 1

            if stagnation_counter >= self.stagnation_limit:
                if self.verbose:
                    print(f"Остановка на итерации {iteration}: стагнация {self.stagnation_limit} шагов")
                break

        final_population = np.array(population)
        self.history.append(final_population.copy())
        self.best_history.append(self.best_value)
        self.best_positions_history.append(self.best_position.copy() if self.best_position is not None else None)

        if self.verbose:
            print("\nОптимизация завершена!")
            print(f"Лучшее значение: {self.best_value:.12f}")
            print(f"Лучшая позиция: {self.best_position}")

        return self.best_position, self.best_value, self.history
