import numpy as np
from typing import Callable, List, Optional, Tuple


class BacterialForagingOptimization:
    """
    Бактериальная оптимизация (BFO) для глобального поиска минимума.
    """

    def __init__(
        self,
        func: Callable,
        bounds: np.ndarray,
        n_bacteria: int = 20,
        chemotaxis_steps: int = 12,
        swim_length: int = 4,
        reproduction_steps: int = 6,
        elimination_steps: int = 2,
        step_size: float = 0.12,
        elimination_probability: float = 0.2,
        max_iterations: int = 144,
        stagnation_limit: int = 30,
        verbose: bool = False,
    ):
        self.func = func
        self.bounds = np.array(bounds, dtype=float)
        self.dimension = len(bounds)

        self.n_bacteria = n_bacteria
        self.chemotaxis_steps = chemotaxis_steps
        self.swim_length = swim_length
        self.reproduction_steps = reproduction_steps
        self.elimination_steps = elimination_steps
        self.step_size = step_size
        self.elimination_probability = elimination_probability
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

    def _tumble(self, position: np.ndarray) -> np.ndarray:
        direction = np.random.normal(size=self.dimension)
        norm = np.linalg.norm(direction)
        if norm < 1e-12:
            direction = np.ones(self.dimension)
            norm = np.linalg.norm(direction)

        normalized_direction = direction / norm
        step = normalized_direction * self.step_size * (self.bounds[:, 1] - self.bounds[:, 0])
        return np.clip(position + step, self.bounds[:, 0], self.bounds[:, 1])

    def solve(self, real_time_callback: Optional[Callable] = None) -> Tuple[np.ndarray, float, List[np.ndarray]]:
        self.history = []
        self.best_history = []
        self.best_positions_history = []
        self.best_position = None
        self.best_value = float("inf")

        bacteria = [self._random_position() for _ in range(self.n_bacteria)]
        values = [self._evaluate(point) for point in bacteria]
        health = np.zeros(self.n_bacteria)

        iteration = 0
        stagnation_counter = 0
        last_best_value = float("inf")

        for elimination_step in range(self.elimination_steps):
            for reproduction_step in range(self.reproduction_steps):
                health.fill(0.0)

                for _ in range(self.chemotaxis_steps):
                    if iteration >= self.max_iterations:
                        break

                    for i in range(self.n_bacteria):
                        current_value = values[i]
                        health[i] += current_value

                        new_position = self._tumble(bacteria[i])
                        new_value = self._evaluate(new_position)

                        swim_counter = 0
                        while new_value < current_value and swim_counter < self.swim_length:
                            bacteria[i] = new_position
                            current_value = new_value
                            values[i] = new_value

                            new_position = self._tumble(bacteria[i])
                            new_value = self._evaluate(new_position)
                            swim_counter += 1

                        if values[i] < self.best_value:
                            self.best_value = values[i]
                            self.best_position = bacteria[i].copy()

                    current_population = np.array(bacteria)
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

                    if self.best_value < last_best_value:
                        stagnation_counter = 0
                        last_best_value = self.best_value
                    else:
                        stagnation_counter += 1

                    iteration += 1

                    if stagnation_counter >= self.stagnation_limit:
                        break

                if iteration >= self.max_iterations or stagnation_counter >= self.stagnation_limit:
                    break

                order = np.argsort(health)
                half = self.n_bacteria // 2
                best_half = [bacteria[i].copy() for i in order[:half]]
                bacteria = best_half + [point.copy() for point in best_half]
                values = [self._evaluate(point) for point in bacteria]
                health = np.zeros(self.n_bacteria)

                if iteration >= self.max_iterations or stagnation_counter >= self.stagnation_limit:
                    break

            for i in range(self.n_bacteria):
                if np.random.rand() < self.elimination_probability:
                    bacteria[i] = self._random_position()
                    values[i] = self._evaluate(bacteria[i])
                    if values[i] < self.best_value:
                        self.best_value = values[i]
                        self.best_position = bacteria[i].copy()

            if iteration >= self.max_iterations or stagnation_counter >= self.stagnation_limit:
                break

        final_population = np.array(bacteria)
        self.history.append(final_population.copy())
        self.best_history.append(self.best_value)
        self.best_positions_history.append(self.best_position.copy() if self.best_position is not None else None)

        if self.verbose:
            print("\nОптимизация завершена!")
            print(f"Лучшее значение: {self.best_value:.12f}")
            print(f"Лучшая позиция: {self.best_position}")

        return self.best_position, self.best_value, self.history
