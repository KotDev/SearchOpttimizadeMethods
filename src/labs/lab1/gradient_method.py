import numpy as np


class GradientMethod:
    """Базовый класс для градиентных методов оптимизации"""

    def __init__(self, name: str):
        self.name = name
        self.trajectory = []
        self.grad_norms = []
        self.f_values = []
        self.iterations = 0

    def minimize(self, func, x0, max_iter=100, epsilon=1e-6, **kwargs):
        self.trajectory = [np.array(x0, dtype=float)]
        self.grad_norms = []
        self.f_values = [func(x0)]
        x = np.array(x0, dtype=float)
        f_current = self.f_values[0]

        for k in range(max_iter):
            grad = func.gradient(x)
            grad_norm = np.linalg.norm(grad)
            self.grad_norms.append(grad_norm)

            if grad_norm < epsilon:
                self.iterations = k + 1
                break

            # Проверка на расходимость (слишком большие значения текущей точки)
            if np.any(np.abs(x) > 1e6):
                print(f"Warning: Divergence detected at iteration {k} (x too large)")
                self.iterations = k + 1
                break

            # Передаем предыдущее значение функции для адаптивных шагов
            step_kwargs = dict(kwargs)
            step_kwargs["prev_f"] = f_current

            x_new = self._step(x, grad, func, k, **step_kwargs)

            # Проверка на NaN и расходимость новой точки
            if np.any(np.isnan(x_new)) or np.any(np.abs(x_new) > 1e6):
                print(f"Warning: Divergence detected at iteration {k} (x_new invalid)")
                self.iterations = k + 1
                break

            self.trajectory.append(x_new.copy())
            x = x_new
            f_current = func(x)
            self.f_values.append(f_current)
            self.iterations = k + 1

        return x, self.trajectory, self.iterations

    def _step(self, x, grad, func, k, **kwargs):
        raise NotImplementedError

    def get_convergence_info(self):
        return {
            'iterations': self.iterations,
            'final_grad_norm': self.grad_norms[-1] if self.grad_norms else None,
            'final_value': self.f_values[-1] if self.f_values else None,
            'grad_norms': self.grad_norms,
            'f_values': self.f_values
        }