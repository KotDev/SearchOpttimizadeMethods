from typing import Union

import numpy as np

from src.test_functions.abstract_test_functions import TestFunction


class RosenbrockFunction(TestFunction):
    """
    Функция Розенброка (банановая).
    Глобальный минимум: f(1,1,...,1) = 0
    """

    def __init__(self, dim: int = 2):
        super().__init__(f"Функция Розенброка (dim={dim})", dim)
        self._optimal_point = np.ones(dim)
        self._optimal_value = 0.0
        self._bounds = np.array([[-2.0, 2.0]] * dim)

    def _evaluate(self, x: np.ndarray) -> float:
        result = 0.0
        for i in range(self.dim - 1):
            result += 100 * (x[i + 1] - x[i] ** 2) ** 2 + (1 - x[i]) ** 2
        return result

    def gradient(self, x: Union[np.ndarray, list, tuple]) -> np.ndarray:
        """
        Аналитический градиент для функции Розенброка.
        """
        x = np.asarray(x, dtype=float)
        grad = np.zeros_like(x)

        for i in range(self.dim - 1):
            grad[i] += -400 * x[i] * (x[i + 1] - x[i] ** 2) - 2 * (1 - x[i])
            grad[i + 1] += 200 * (x[i + 1] - x[i] ** 2)

        return grad