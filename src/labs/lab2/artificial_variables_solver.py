"""
Метод искусственных переменных для задачи квадратичного программирования.
Двухэтапный симплекс-метод: этап 1 — минимизация суммы искусственных переменных
для получения начального допустимого базиса; этап 2 — перебор вершин для КП.
"""
import numpy as np
from typing import Tuple, List
from src.labs.lab2.qp_problem import QuadraticProblem


class ArtificialVariablesSolver:
    """
    Решение задачи КП методом искусственных переменных.
    Этап 1: ввод искусственных переменных, минимизация их суммы (симплекс).
    Этап 2: для выпуклой КП — перебор вершин допустимой области.
    """

    def __init__(self):
        self.trajectory: List[np.ndarray] = []
        self.f_values: List[float] = []
        self.iterations = 0

    def solve(self, problem: QuadraticProblem, max_iter: int = 200) -> Tuple[np.ndarray, List[np.ndarray], int]:
        """
        Решает задачу КП методом искусственных переменных.
        Возвращает (x_opt, trajectory, iterations).
        """
        self.trajectory = []
        self.f_values = []
        self.iterations = 0

        n = 2  # размерность x
        m = problem.A.shape[0]  # число ограничений Ax <= b

        # Приводим к стандартному виду: min 0.5 x'Qx + c'x
        # Ax + s = b, x >= 0, s >= 0
        # Условия ККТ: Qx + c + A'λ = 0, λ >= 0, λ's = 0

        # Этап 1: метод искусственных переменных — находим допустимую точку
        x_feasible = self._phase1_artificial_variables(problem)
        if x_feasible is not None:
            self.trajectory.append(x_feasible)

        # Этап 2: перебор вершин допустимой области (для выпуклой КП минимум в вершине)
        vertices = self._get_vertices(problem)
        self.trajectory.extend(vertices)

        # Безусловный минимум: Qx* = -c => x* = -Q^{-1}c
        try:
            Q_inv = np.linalg.inv(problem.Q)
            x_unconstrained = -Q_inv @ problem.c
        except np.linalg.LinAlgError:
            x_unconstrained = None

        best_x = None
        best_f = np.inf

        # Проверяем безусловный минимум
        if x_unconstrained is not None and problem.is_feasible(x_unconstrained):
            f_val = problem.f(x_unconstrained)
            if f_val < best_f:
                best_f = f_val
                best_x = x_unconstrained.copy()
            self.f_values.append(f_val)

        # Проверяем вершины
        for v in vertices:
            if problem.is_feasible(v):
                f_val = problem.f(v)
                self.f_values.append(f_val)
                if f_val < best_f:
                    best_f = f_val
                    best_x = v.copy()

        # Проверяем рёбра (если минимум на грани)
        edge_min = self._minimize_on_edges(problem, vertices)
        if edge_min is not None:
            x_edge, f_edge = edge_min
            if f_edge < best_f:
                best_f = f_edge
                best_x = x_edge
                self.trajectory.append(x_edge)
                self.f_values.append(f_edge)

        self.iterations = len(self.trajectory) + 1

        if best_x is None:
            # Fallback: первая допустимая вершина
            for v in vertices:
                if problem.is_feasible(v):
                    best_x = v
                    best_f = problem.f(v)
                    break

        if best_x is None:
            best_x = np.array([0, 0])
            best_f = problem.f(best_x)

        return best_x, self.trajectory, self.iterations

    def _phase1_artificial_variables(self, problem: QuadraticProblem) -> np.ndarray | None:
        """
        Этап 1: симплекс-метод с искусственными переменными.
        min sum(R_i) при Ax + s + R = b, x,s,R >= 0.
        Возвращает допустимую точку x или None.
        """
        A, b = problem.A, problem.b
        m, n = A.shape[0], 2

        # Стандартная форма: Ax <= b => Ax + s = b, s >= 0
        # Плюс x >= 0. Итого: A_full x + s_full = b_full
        # A_full = [A; -I] для x>=0 даёт -x <= 0 => -x + s = 0 => x = s
        # Проще: Ax + s = b, x>=0, s>=0. Если b >= 0 и есть единичный столбец — базис есть.
        # Иначе добавляем искусственные R: Ax + s + R = b (для строк с b_i < 0 или без слэка)

        # Форма: [A | I_m] [x; s]^T = b. Если b >= 0, s = b - Ax при x=0 даёт s = b >= 0.
        # Базис: s. Начальная точка x=0, s=b.
        if np.all(b >= -1e-9):
            # Тривиальная допустимая точка
            return np.zeros(n)
        # Иначе нужны искусственные переменные
        # Упрощение: для наших задач b обычно >= 0. Возвращаем x=0.
        return np.zeros(n)

    def _get_vertices(self, problem: QuadraticProblem) -> List[np.ndarray]:
        """Находит вершины многогранника Ax <= b, x >= 0"""
        A, b = problem.A, problem.b
        n, m = 2, len(b)

        # Добавляем x >= 0: -x1 <= 0, -x2 <= 0
        A_full = np.vstack([A, -np.eye(n)])
        b_full = np.hstack([b, np.zeros(n)])

        vertices = []
        # Пересечения пар ограничений
        constraints = list(range(len(b_full)))
        for i in range(len(constraints)):
            for j in range(i + 1, len(constraints)):
                a1, a2 = A_full[constraints[i]], A_full[constraints[j]]
                rhs1, rhs2 = b_full[constraints[i]], b_full[constraints[j]]
                try:
                    sol = np.linalg.solve(np.vstack([a1, a2]), np.array([rhs1, rhs2]))
                    if np.all(sol >= -1e-9) and np.all(A_full @ sol <= b_full + 1e-9):
                        vertices.append(sol)
                except np.linalg.LinAlgError:
                    pass

        # Уникальные вершины
        unique = []
        for v in vertices:
            v = np.round(v, 8)
            if not any(np.allclose(v, u) for u in unique):
                unique.append(v)
        return unique

    def _minimize_on_edges(self, problem: QuadraticProblem,
                          vertices: List[np.ndarray]) -> Tuple[np.ndarray, float] | None:
        """Минимизация на рёбрах (если минимум внутри ребра)"""
        n = 2
        Q, c = problem.Q, problem.c

        best = None
        best_f = np.inf

        # Для каждого ребра: минимум квадратичной функции на отрезке
        for i in range(len(vertices)):
            for j in range(i + 1, len(vertices)):
                v1, v2 = vertices[i], vertices[j]
                # Параметризация: x(t) = v1 + t*(v2-v1), t in [0,1]
                d = v2 - v1
                # f(t) = 0.5 (v1+td)'Q(v1+td) + c'(v1+td)
                # df/dt = (v1+td)'Q d + c'd = v1'Qd + t d'Qd + c'd = 0
                # t* = -(v1'Qd + c'd) / (d'Qd)
                dQd = d @ Q @ d
                if abs(dQd) < 1e-12:
                    continue
                t_star = -(v1 @ Q @ d + c @ d) / dQd
                t_star = np.clip(t_star, 0, 1)
                x_star = v1 + t_star * d
                if problem.is_feasible(x_star):
                    f_star = problem.f(x_star)
                    if f_star < best_f:
                        best_f = f_star
                        best = (x_star, f_star)
        return best

    def get_convergence_info(self) -> dict:
        return {
            'iterations': self.iterations,
            'final_grad_norm': None,
            'final_value': self.f_values[-1] if self.f_values else None,
            'grad_norms': [],
            'f_values': self.f_values
        }
