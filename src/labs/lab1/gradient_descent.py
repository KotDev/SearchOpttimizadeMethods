from src.labs.lab1.gradient_method import GradientMethod


class GradientDescent(GradientMethod):
    """Метод градиентного спуска с постоянным шагом"""

    def __init__(self, step_size=0.01, adaptive=True):
        super().__init__("Градиентный спуск с постоянным шагом")
        self.step_size = step_size
        self.adaptive = adaptive

    def _step(self, x, grad, func, k, **kwargs):
        """
        Один шаг градиентного спуска.
        Для устойчивости используем простую одномерную подстройку шага:
        пытаемся уменьшать f(x - alpha * grad) по альфе, пока значение не перестанет расти
        и пока точка не выйдет далеко за разумные пределы.
        """
        # Базовый шаг из параметров
        base_step = self.step_size
        alpha = base_step

        f_current = func(x)

        # Небольшой внутренний цикл "бэктрекинг" по шагу
        for _ in range(20):
            x_new = x - alpha * grad

            # Защита от вылета далеко наружу
            if (abs(x_new) > 1e3).any():
                alpha *= 0.5
                continue

            f_new = func(x_new)

            # Принимаем шаг, если функция не растёт
            if f_new <= f_current:
                # Обновляем текущий шаг в сторону найденного (делаем метод более устойчивым)
                if self.adaptive:
                    self.step_size = max(alpha, 1e-6)
                return x_new

            # Иначе уменьшаем шаг
            alpha *= 0.5

        # Если за ограниченное число попыток ничего хорошего не нашли —
        # делаем очень маленький шаг, лишь бы не взорваться
        alpha = max(self.step_size * 0.1, 1e-6)
        x_new = x - alpha * grad
        if self.adaptive:
            self.step_size = alpha
        return x_new
