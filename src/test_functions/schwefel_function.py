import numpy as np

from src.test_functions.abstract_test_functions import TestFunction


class SchwefelFunction(TestFunction):
    """
    Функция Швефеля.
    Глобальный минимум: f(420.9687,...,420.9687) ≈ 0
    """

    def __init__(self, dim: int = 2):
        super().__init__(f"Функция Швефеля (dim={dim})", dim)
        self._optimal_point = np.full(dim, 420.9687)
        self._optimal_value = 0.0
        self._bounds = np.array([[-500.0, 500.0]] * dim)

    def _evaluate(self, x: np.ndarray) -> float:
        return 418.9829 * self.dim - np.sum(x * np.sin(np.sqrt(np.abs(x))))
