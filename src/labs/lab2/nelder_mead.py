import numpy as np
from src.labs.lab2.direct_search_method import DirectSearchMethod


class NelderMead(DirectSearchMethod):
    """
    Метод Нелдера-Мида (симплекс-метод, деформируемый многогранник).
    Прямой метод без производных. Использует симплекс из n+1 вершин.
    """

    def __init__(self, alpha=1.0, gamma=2.0, rho=0.5, sigma=0.5):
        super().__init__("Нелдер-Мида")
        self.alpha = alpha   # коэффициент отражения
        self.gamma = gamma   # коэффициент растяжения
        self.rho = rho       # коэффициент сжатия
        self.sigma = sigma   # коэффициент сжатия симплекса

    def minimize(self, func, x0, max_iter=100, epsilon=1e-6, **kwargs):
        self.trajectory = [np.array(x0, dtype=float)]
        self.f_values = [func(x0)]
        self.iterations = 0

        n = len(x0)
        # Инициализация симплекса
        simplex = self._init_simplex(np.array(x0, dtype=float), n)
        f_simplex = np.array([func(v) for v in simplex])

        for _ in range(max_iter):
            # Сортируем по значению функции (лучший - первый)
            order = np.argsort(f_simplex)
            simplex = simplex[order]
            f_simplex = f_simplex[order]

            # Лучшая и худшая точки
            x_best = simplex[0]
            x_worst = simplex[-1]
            f_worst = f_simplex[-1]
            f_best = f_simplex[0]

            # Центроид (без худшей точки)
            centroid = np.mean(simplex[:-1], axis=0)

            # Отражение
            x_reflect = centroid + self.alpha * (centroid - x_worst)
            f_reflect = func(x_reflect)

            if f_reflect < f_best:
                # Растяжение
                x_expand = centroid + self.gamma * (x_reflect - centroid)
                f_expand = func(x_expand)
                if f_expand < f_reflect:
                    simplex[-1] = x_expand
                    f_simplex[-1] = f_expand
                else:
                    simplex[-1] = x_reflect
                    f_simplex[-1] = f_reflect
            elif f_reflect < f_simplex[-2]:
                # Принимаем отражение
                simplex[-1] = x_reflect
                f_simplex[-1] = f_reflect
            else:
                # Сжатие
                if f_reflect < f_worst:
                    x_contract = centroid + self.rho * (x_reflect - centroid)
                else:
                    x_contract = centroid + self.rho * (x_worst - centroid)
                f_contract = func(x_contract)

                if f_contract < f_worst:
                    simplex[-1] = x_contract
                    f_simplex[-1] = f_contract
                else:
                    # Редукция симплекса к лучшей точке
                    for i in range(1, n + 1):
                        simplex[i] = x_best + self.sigma * (simplex[i] - x_best)
                        f_simplex[i] = func(simplex[i])

            self.trajectory.append(simplex[0].copy())
            self.f_values.append(f_simplex[0])
            self.iterations += 1

            # Критерий остановки
            std = np.std(f_simplex)
            if std < epsilon:
                break
            if np.linalg.norm(simplex[-1] - simplex[0]) < epsilon:
                break

        x_opt = simplex[0]
        return x_opt, self.trajectory, self.iterations

    def _init_simplex(self, x0, n):
        """Инициализация симплекса: x0 и n точек со смещением по координатам"""
        simplex = np.zeros((n + 1, n))
        simplex[0] = x0
        scale = max(1.0, np.linalg.norm(x0) * 0.1)
        for i in range(n):
            simplex[i + 1] = x0.copy()
            simplex[i + 1][i] += scale
        return simplex
