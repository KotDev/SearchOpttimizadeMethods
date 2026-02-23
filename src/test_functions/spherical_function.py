from typing import Union

import numpy as np

from src.test_functions.abstract_test_functions import TestFunction


class SphericalFunction(TestFunction):
    """
    Сферическая функция (простая квадратичная).
    Глобальный минимум: f(0,...,0) = 0
    """

    def __init__(self, dim: int = 2):
        super().__init__(f"Сферическая функция (dim={dim})", dim)
        self._optimal_point = np.zeros(dim)
        self._optimal_value = 0.0
        self._bounds = np.array([[-5.0, 5.0]] * dim)

    def _evaluate(self, x: np.ndarray) -> float:
        return np.sum(x ** 2)

    def gradient(self, x: Union[np.ndarray, list, tuple]) -> np.ndarray:
        return 2 * np.asarray(x)