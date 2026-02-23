from src.test_functions.abstract_test_functions import TestFunction
from src.test_functions.ackley_function import AckleyFunction
from src.test_functions.griewank_function import GriewankFunction
from src.test_functions.himmelblau_function import HimmelblauFunction
from src.test_functions.rastrigin_function import RastriginFunction
from src.test_functions.rosenborck_function import RosenbrockFunction
from src.test_functions.schwefel_function import SchwefelFunction
from src.test_functions.spherical_function import SphericalFunction


class TestFunctionFactory:
    """
    Фабрика для создания тестовых функций любой размерности.
    """

    @staticmethod
    def create(name: str, dim: int = 2, **kwargs) -> TestFunction:
        """
        Создание функции по имени.

        Args:
            name: Название функции
            dim: Размерность
            **kwargs: Дополнительные параметры

        Returns:
            Экземпляр тестовой функции
        """
        functions = {
            'rosenbrock': RosenbrockFunction,
            'himmelblau': HimmelblauFunction,
            'rastrigin': RastriginFunction,
            'ackley': AckleyFunction,
            'spherical': SphericalFunction,
            'griewank': GriewankFunction,
            'schwefel': SchwefelFunction
        }

        name_lower = name.lower()
        for key, func_class in functions.items():
            if key in name_lower:
                if key == 'himmelblau' and dim != 2:
                    raise ValueError("Функция Химмельблау только для 2D")
                return func_class(dim=dim, **kwargs)

        raise ValueError(f"Неизвестная функция: {name}")

    @staticmethod
    def create_all(dim: int = 2) -> list:
        """
        Создание всех доступных функций.

        Args:
            dim: Размерность

        Returns:
            Список функций
        """
        functions = [
            RosenbrockFunction(dim),
            RastriginFunction(dim),
            AckleyFunction(dim),
            SphericalFunction(dim),
            GriewankFunction(dim),
            SchwefelFunction(dim)
        ]

        if dim == 2:
            functions.append(HimmelblauFunction())

        return functions

    @staticmethod
    def create_by_dimension(dim: int) -> list:
        """
        Создание функций, подходящих для данной размерности.

        Args:
            dim: Размерность

        Returns:
            Список подходящих функций
        """
        functions = []

        # Всегда доступны
        functions.extend([
            RosenbrockFunction(dim),
            RastriginFunction(dim),
            AckleyFunction(dim),
            SphericalFunction(dim),
            GriewankFunction(dim),
            SchwefelFunction(dim)
        ])

        # Специальные случаи
        if dim == 2:
            functions.append(HimmelblauFunction())

        return functions
