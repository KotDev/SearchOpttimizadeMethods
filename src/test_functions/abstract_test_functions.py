import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, Optional, Callable, Dict, Any, Union
import json


class TestFunction(ABC):
    """
    Универсальный абстрактный базовый класс для тестовых функций оптимизации.
    Может использоваться в любых алгоритмах: градиентных, эволюционных,
    роевых, симулированном отжиге и т.д.
    """

    def __init__(self, name: str, dim: int = 2):
        """
        Инициализация тестовой функции.

        Args:
            name: Название функции
            dim: Размерность пространства (по умолчанию 2 для визуализации)
        """
        self.name = name
        self.dim = dim
        self.evaluations = 0  # Счетчик вызовов для оценки сложности
        self._bounds = None  # Границы области поиска
        self._optimal_value = None  # Оптимальное значение
        self._optimal_point = None  # Оптимальная точка

    def __call__(self, x: Union[np.ndarray, list, tuple]) -> float:
        """
        Вычисление значения функции.

        Args:
            x: Точка в пространстве параметров

        Returns:
            Значение функции
        """
        self.evaluations += 1
        return self._evaluate(np.asarray(x, dtype=float))

    @abstractmethod
    def _evaluate(self, x: np.ndarray) -> float:
        """
        Внутренний метод вычисления значения (переопределяется в наследниках).
        """
        pass

    def gradient(self, x: Union[np.ndarray, list, tuple],
                 eps: float = 1e-7) -> np.ndarray:
        """
        Вычисление градиента численным методом (по умолчанию).
        Может быть переопределен для аналитического градиента.

        Args:
            x: Точка для вычисления градиента
            eps: Шаг дифференцирования

        Returns:
            Вектор градиента
        """
        x = np.asarray(x, dtype=float)
        grad = np.zeros_like(x)

        for i in range(len(x)):
            x_plus = x.copy()
            x_minus = x.copy()
            x_plus[i] += eps
            x_minus[i] -= eps
            grad[i] = (self(x_plus) - self(x_minus)) / (2 * eps)

        return grad

    def hessian(self, x: Union[np.ndarray, list, tuple],
                eps: float = 1e-5) -> np.ndarray:
        """
        Вычисление матрицы Гессе численным методом.

        Args:
            x: Точка для вычисления Гессе
            eps: Шаг дифференцирования

        Returns:
            Матрица Гессе
        """
        x = np.asarray(x, dtype=float)
        n = len(x)
        hess = np.zeros((n, n))

        for i in range(n):
            for j in range(i, n):
                if i == j:
                    # Вторая производная по одной переменной
                    x_plus = x.copy()
                    x_minus = x.copy()
                    x_plus[i] += eps
                    x_minus[i] -= eps
                    hess[i, i] = (self(x_plus) - 2 * self(x) + self(x_minus)) / (eps ** 2)
                else:
                    # Смешанная производная
                    x_pp = x.copy()
                    x_pm = x.copy()
                    x_mp = x.copy()
                    x_mm = x.copy()

                    x_pp[i] += eps
                    x_pp[j] += eps

                    x_pm[i] += eps
                    x_pm[j] -= eps

                    x_mp[i] -= eps
                    x_mp[j] += eps

                    x_mm[i] -= eps
                    x_mm[j] -= eps

                    hess[i, j] = hess[j, i] = (self(x_pp) - self(x_pm) -
                                               self(x_mp) + self(x_mm)) / (4 * eps ** 2)

        return hess

    @property
    def bounds(self) -> np.ndarray:
        """
        Границы области поиска (по умолчанию [-5, 5] для каждой размерности).
        """
        if self._bounds is None:
            self._bounds = np.array([[-5.0, 5.0]] * self.dim)
        return self._bounds

    @bounds.setter
    def bounds(self, bounds: Union[np.ndarray, list, tuple]):
        """
        Установка границ области поиска.
        """
        bounds = np.asarray(bounds, dtype=float)
        if bounds.shape == (self.dim, 2):
            self._bounds = bounds
        else:
            raise ValueError(f"bounds must have shape ({self.dim}, 2)")

    @property
    def optimal_value(self) -> Optional[float]:
        """
        Известное оптимальное значение (если есть).
        """
        return self._optimal_value

    @property
    def optimal_point(self) -> Optional[np.ndarray]:
        """
        Известная оптимальная точка (если есть).
        """
        return self._optimal_point

    def is_optimal(self, x: Union[np.ndarray, list, tuple],
                   tolerance: float = 1e-6) -> bool:
        """
        Проверка, является ли точка оптимальной.

        Args:
            x: Проверяемая точка
            tolerance: Допустимая погрешность

        Returns:
            True если точка близка к оптимальной
        """
        if self.optimal_point is None:
            return False
        return np.linalg.norm(np.asarray(x) - self.optimal_point) < tolerance

    def random_point(self, bounds: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Генерация случайной точки в заданных границах.

        Args:
            bounds: Границы (если None, используются self.bounds)

        Returns:
            Случайная точка
        """
        if bounds is None:
            bounds = self.bounds

        point = np.zeros(self.dim)
        for i in range(self.dim):
            point[i] = np.random.uniform(bounds[i, 0], bounds[i, 1])
        return point

    def reset_evaluations(self):
        """Сброс счетчика вычислений."""
        self.evaluations = 0

    def get_info(self) -> Dict[str, Any]:
        """
        Получение информации о функции.
        """
        return {
            'name': self.name,
            'dimension': self.dim,
            'bounds': self.bounds.tolist(),
            'optimal_value': self.optimal_value,
            'optimal_point': self.optimal_point.tolist() if self.optimal_point is not None else None,
            'evaluations': self.evaluations
        }

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', dim={self.dim})"