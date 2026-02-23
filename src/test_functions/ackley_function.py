from typing import Union

import numpy as np

from src.test_functions.abstract_test_functions import TestFunction


class AckleyFunction(TestFunction):
    """
    Функция Аклея.
    Глобальный минимум: f(0,...,0) = 0
    """

    def __init__(self, dim: int = 2):
        super().__init__(f"Функция Аклея (dim={dim})", dim)
        self._optimal_point = np.zeros(dim)
        self._optimal_value = 0.0
        self._bounds = np.array([[-5.0, 5.0]] * dim)

    def _evaluate(self, x: np.ndarray) -> float:
        sum1 = np.sum(x ** 2)
        sum2 = np.sum(np.cos(2 * np.pi * x))

        term1 = -20 * np.exp(-0.2 * np.sqrt(sum1 / self.dim))
        term2 = -np.exp(sum2 / self.dim)

        return term1 + term2 + 20 + np.e

    def gradient(self, x: Union[np.ndarray, list, tuple],
                 eps: float = 1e-7) -> np.ndarray:
        # Для сложных функций используем численный градиент
        return super().gradient(x, eps)
