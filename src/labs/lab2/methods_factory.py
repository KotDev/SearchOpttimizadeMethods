from src.labs.lab2.hooke_jeeves import HookeJeeves
from src.labs.lab2.nelder_mead import NelderMead
from src.labs.lab2.powell import Powell


class Lab2MethodFactory:
    """Фабрика для создания методов прямого поиска (ЛР2)"""

    @staticmethod
    def create(method_name, **kwargs):
        if method_name == "Хука-Дживса":
            step = kwargs.get('step', 0.5)
            step_reduction = kwargs.get('step_reduction', 0.5)
            return HookeJeeves(step=step, step_reduction=step_reduction)

        elif method_name == "Нелдер-Мида":
            return NelderMead()

        elif method_name == "Пауэлла":
            return Powell()

        else:
            return HookeJeeves()
