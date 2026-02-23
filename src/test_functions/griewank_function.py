import numpy as np

from src.test_functions.abstract_test_functions import TestFunction


class GriewankFunction(TestFunction):
    """
    Функция Гриванка.
    Глобальный минимум: f(0,...,0) = 0
    """

    def __init__(self, dim: int = 2):
        super().__init__(f"Функция Гриванка (dim={dim})", dim)
        self._optimal_point = np.zeros(dim)
        self._optimal_value = 0.0
        self._bounds = np.array([[-600.0, 600.0]] * dim)

    def _evaluate(self, x: np.ndarray) -> float:
        sum_part = np.sum(x ** 2) / 4000
        prod_part = np.prod(np.cos(x / np.sqrt(np.arange(1, self.dim + 1))))
        return sum_part - prod_part + 1
