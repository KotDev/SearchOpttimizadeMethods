import numpy as np

from src.labs.lab1.gradient_method import GradientMethod


class NewtonRaphson(GradientMethod):
    """Метод Ньютона-Рафсона"""

    def __init__(self, damping=1.0, regularization=1e-8, max_step=1.0):
        super().__init__("Ньютон-Рафсон")
        self.damping = damping
        self.regularization = regularization
        self.max_step = max_step

    def _step(self, x, grad, func, k, **kwargs):
        H = func.hessian(x)

        # Регуляризация
        H_reg = H + self.regularization * np.eye(len(x))

        try:
            delta = np.linalg.solve(H_reg, -grad)

            # Ограничиваем шаг
            delta_norm = np.linalg.norm(delta)
            if delta_norm > self.max_step:
                delta = delta / delta_norm * self.max_step

            return x + self.damping * delta

        except np.linalg.LinAlgError:
            # Если матрица вырождена, используем градиентный шаг
            return x - 0.1 * grad