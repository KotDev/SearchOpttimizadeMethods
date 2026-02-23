import numpy as np

from src.labs.lab1.gradient_method import GradientMethod


class CoordinateDescent(GradientMethod):
    """Метод покоординатного спуска"""

    def __init__(self, step_size=0.1, adaptive=True):
        super().__init__("Покоординатный спуск")
        self.step_size = step_size
        self.adaptive = adaptive

    def _step(self, x, grad, func, k, **kwargs):
        x_new = x.copy()
        f_current = func(x)

        # Адаптивный шаг
        current_step = self.step_size
        if self.adaptive and k > 0:
            if f_current > kwargs.get('prev_f', float('inf')):
                current_step *= 0.9

        for i in range(len(x)):
            # Пробуем положительный шаг
            step = current_step * np.sign(-grad[i])
            x_test = x_new.copy()
            x_test[i] += step

            # Проверка на слишком большие значения
            if np.any(np.abs(x_test) > 1e6):
                continue

            f_test = func(x_test)
            if f_test < f_current:
                x_new[i] = x_test[i]
                f_current = f_test

        return x_new
