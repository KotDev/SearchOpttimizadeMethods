"""
Задачи квадратичного программирования.
min 0.5 x'Qx + c'x  при  Ax <= b, x >= 0
или max для невыпуклых задач
"""
import numpy as np
from dataclasses import dataclass
from typing import Optional, List, Tuple


@dataclass
class QuadraticProblem:
    """Задача КП: min 0.5 x'Qx + c'x, s.t. Ax <= b, x >= 0"""
    name: str
    Q: np.ndarray  # матрица 2x2 (симметричная)
    c: np.ndarray  # вектор 2x1
    A: np.ndarray  # матрица ограничений m x 2
    b: np.ndarray  # вектор m x 1
    is_maximization: bool = False  # флаг для задачи максимизации
    optimal_point: Optional[np.ndarray] = None
    optimal_value: Optional[float] = None

    def f(self, x: np.ndarray) -> float:
        """Значение целевой функции (для min или max)"""
        x = np.asarray(x, dtype=float).ravel()
        val = 0.5 * x @ self.Q @ x + self.c @ x
        return val

    def is_feasible(self, x: np.ndarray, tol: float = 1e-9) -> bool:
        """Проверка допустимости точки"""
        x = np.asarray(x, dtype=float).ravel()
        if np.any(x < -tol):
            return False
        return np.all(self.A @ x <= self.b + tol)

    @property
    def bounds(self) -> np.ndarray:
        """Границы для визуализации (по ограничениям)"""
        x_min, x_max = 0, 5
        y_min, y_max = 0, 5
        for i in range(len(self.b)):
            a1, a2 = self.A[i, 0], self.A[i, 1]
            rhs = self.b[i]
            if abs(a2) > 1e-10:
                # y = (rhs - a1*x) / a2
                for x_test in [0, 5]:
                    y_val = (rhs - a1 * x_test) / a2
                    if 0 <= y_val <= 5:
                        y_min = min(y_min, y_val)
                        y_max = max(y_max, y_val)
            if abs(a1) > 1e-10:
                for y_test in [0, 5]:
                    x_val = (rhs - a2 * y_test) / a1
                    if 0 <= x_val <= 5:
                        x_min = min(x_min, x_val)
                        x_max = max(x_max, x_val)
        return np.array([[max(0, x_min - 0.5), x_max + 0.5],
                         [max(0, y_min - 0.5), y_max + 0.5]])

    def check_kkt_conditions(self, x: np.ndarray, tol: float = 1e-6) -> np.ndarray:
        """
        Проверка условий Куна-Таккера
        
        Args:
            x: точка для проверки
            tol: точность вычислений
            
        Returns:
            Множители Лагранжа для активных ограничений
        """
        x = np.asarray(x, dtype=float).ravel()
        
        # Находим активные ограничения (где Ax ≈ b)
        residuals = self.A @ x - self.b
        active_mask = np.abs(residuals) < tol
        active_indices = np.where(active_mask)[0]
        
        if len(active_indices) > 0:
            # Берем только активные ограничения
            A_active = self.A[active_indices]
            
            # Градиент целевой функции: ∇f(x) = Qx + c
            grad_f = self.Q @ x + self.c
            
            try:
                # Решаем систему A_active^T * λ = -grad_f
                # Это переопределенная система, используем наименьшие квадраты
                lambda_vals, residuals, rank, s = np.linalg.lstsq(
                    A_active.T, -grad_f, rcond=None
                )
                
                print(f"Найденные множители Лагранжа: {lambda_vals}")
                print(f"Активные ограничения: {active_indices}")
                
                return lambda_vals
            except Exception as e:
                print(f"Ошибка при решении системы для λ: {e}")
                return np.array([])
        else:
            print("Нет активных ограничений")
            return np.array([])

class QPProblemFactory:
    """Фабрика задач квадратичного программирования"""

    @staticmethod
    def create_all() -> List[QuadraticProblem]:
        problems = []

        # Задача 1: min f(x) = 2x₁² + 3x₂² + 4x₁x₂ - 6x₁ - 3x₂
        # при x₁ + x₂ ≤ 1, 2x₁ + 3x₂ ≤ 4, x₁ ≥ 0, x₂ ≥ 0
        # В форме 0.5 x'Qx + c'x:
        # 0.5 * (4x₁² + 6x₂² + 8x₁x₂) = 2x₁² + 3x₂² + 4x₁x₂
        Q1 = np.array([[4, 4],   # 2*2x₁² + 2*4x₁x₂/2 = 4x₁² + 4x₁x₂
                       [4, 6]], dtype=float)  # 2*3x₂² + 2*4x₁x₂/2 = 6x₂² + 4x₁x₂
        c1 = np.array([-6, -3], dtype=float)
        A1 = np.array([[1, 1], 
                       [2, 3]], dtype=float)
        b1 = np.array([1, 4], dtype=float)
        
        # Оптимальное решение (найдено аналитически через условия ККТ)
        # Точка лежит на пересечении x₁ + x₂ = 1 и x₁ ≥ 0, x₂ ≥ 0
        # Решение: x₁ = 0.75, x₂ = 0.25
        p1 = QuadraticProblem(
            name="Задача 1: min 2x₁²+3x₂²+4x₁x₂-6x₁-3x₂, x₁+x₂≤1, 2x₁+3x₂≤4, x≥0",
            Q=Q1,
            c=c1,
            A=A1,
            b=b1,
            is_maximization=False,
            optimal_point=np.array([0.75, 0.25]),
            optimal_value=-2.875  # f(0.75,0.25) = 2*0.5625 + 3*0.0625 + 4*0.1875 - 6*0.75 - 3*0.25
        )
        problems.append(p1)

        # Задача 2: max f(x) = x₁ + 2x₂ - x₂²
        # при 3x₁ + 2x₂ ≤ 6, x₁ + 2x₂ ≤ 4, x₁ ≥ 0, x₂ ≥ 0
        # Для максимизации преобразуем в min: -x₁ - 2x₂ + x₂²
        # В форме 0.5 x'Qx + c'x: Q = [[0, 0], [0, 2]], c = [-1, -2]
        Q2 = np.array([[0, 0],
                       [0, 2]], dtype=float)  # 0.5 * 2 * x₂² = x₂²
        c2 = np.array([-1, -2], dtype=float)  # для min задачи
        A2 = np.array([[3, 2],
                       [1, 2]], dtype=float)
        b2 = np.array([6, 4], dtype=float)
        
        # Оптимальное решение (найдено аналитически)
        # Точка лежит на пересечении x₁ + 2x₂ = 4 и x₂ ≥ 0
        # Решение: x₁ = 2, x₂ = 1
        p2 = QuadraticProblem(
            name="Задача 2: max x₁+2x₂-x₂², 3x₁+2x₂≤6, x₁+2x₂≤4, x≥0",
            Q=Q2,
            c=c2,
            A=A2,
            b=b2,
            is_maximization=True,
            optimal_point=np.array([2, 1]),
            optimal_value=3.0  # f_max(2,1) = 2 + 2*1 - 1 = 3
        )
        problems.append(p2)

        return problems


