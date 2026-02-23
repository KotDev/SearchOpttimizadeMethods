from typing import Union

import numpy as np

from src.test_functions.abstract_test_functions import TestFunction


class HimmelblauFunction(TestFunction):
    """
    Функция Химмельблау (только для 2D).
    Имеет 4 равных минимума.
    """

    def __init__(self, dim=2):  # Добавлен параметр dim с значением по умолчанию
        if dim != 2:
            raise ValueError("Функция Химмельблау только для 2D")
        super().__init__("Функция Химмельблау", dim=2)
        # Четыре минимума
        self._optimal_points = [
            np.array([3.0, 2.0]),
            np.array([-2.805118, 3.131312]),
            np.array([-3.779310, -3.283186]),
            np.array([3.584428, -1.848126])
        ]
        self._optimal_point = self._optimal_points[0]  # Один из минимумов
        self._optimal_value = 0.0
        self._bounds = np.array([[-4.0, 4.0], [-4.0, 4.0]])

    def _evaluate(self, x: np.ndarray) -> float:
        return (x[0] ** 2 + x[1] - 11) ** 2 + (x[0] + x[1] ** 2 - 7) ** 2

    def gradient(self, x: Union[np.ndarray, list, tuple]) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        dfdx = 4 * x[0] * (x[0] ** 2 + x[1] - 11) + 2 * (x[0] + x[1] ** 2 - 7)
        dfdy = 2 * (x[0] ** 2 + x[1] - 11) + 4 * x[1] * (x[0] + x[1] ** 2 - 7)
        return np.array([dfdx, dfdy])

    @property
    def optimal_points(self) -> list:
        """Все точки минимума."""
        return self._optimal_points
