from src.labs.lab1.coordinate_descent import CoordinateDescent
from src.labs.lab1.gradient_descent import GradientDescent
from src.labs.lab1.newton_raphson import NewtonRaphson
from src.labs.lab1.steepest_descent import SteepestDescent


class MethodFactory:
    """Фабрика для создания методов оптимизации"""

    @staticmethod
    def create(method_name, **kwargs):
        if method_name == "Градиентный спуск (постоянный шаг)":
            step_size = kwargs.get('step_size', 0.01)  # Уменьшил шаг по умолчанию
            return GradientDescent(step_size=step_size, adaptive=True)

        elif method_name == "Наискорейший спуск":
            return SteepestDescent()

        elif method_name == "Покоординатный спуск":
            step_size = kwargs.get('step_size', 0.01)
            return CoordinateDescent(step_size=step_size, adaptive=True)

        elif method_name == "Ньютон-Рафсон":
            damping = kwargs.get('damping', 0.5)  # Уменьшил демпфирование
            return NewtonRaphson(damping=damping)

        else:
            return GradientDescent(step_size=kwargs.get('step_size', 0.01))
