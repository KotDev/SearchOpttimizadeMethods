import numpy as np

from src.labs.lab1.gradient_method import GradientMethod


class SteepestDescent(GradientMethod):
    """Метод наискорейшего спуска (с оптимальным шагом)"""

    def __init__(self, alpha_init=1.0, beta=0.5, max_line_search=20):
        super().__init__("Наискорейший спуск")
        self.alpha_init = alpha_init
        self.beta = beta
        self.max_line_search = max_line_search

    def _step(self, x, grad, func, k, **kwargs):
        alpha = self.alpha_init
        f_current = func(x)

        for _ in range(self.max_line_search):
            x_new = x - alpha * grad

            # Проверка на слишком большие значения
            if np.any(np.abs(x_new) > 1e6):
                alpha *= self.beta
                continue

            f_new = func(x_new)

            # Условие Армихо
            if f_new < f_current - 1e-4 * alpha * np.dot(grad, grad):
                return x_new
            alpha *= self.beta

        # Если ничего не подошло, возвращаем последний вариант
        return x - alpha * grad