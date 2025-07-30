from .protocol import FiguresProtocol
from .validation import check_method_perimeter, check_method_square


def add_property(cls: FiguresProtocol):
    """
    Добавит классу свойства square и perimeter
    при наличие одноименных get-методов.
    """

    def wrapper(*args, **kwargs):

        if hasattr(cls, 'get_square'):
            setattr(cls, 'square', property(cls.get_square))

        if hasattr(cls, 'get_perimeter'):
            setattr(cls, 'perimeter', property(cls.get_perimeter))

        return cls(*args, **kwargs)

    return wrapper


def calculate_square(figure: FiguresProtocol) -> float:
    """Вернет площадь фигуры, если у неё есть метод get_square."""
    check_method_square(figure)
    return figure.get_square()


def calculate_perimeter(figure: FiguresProtocol) -> int | float:
    """Вернет периметр фигуры, если у неё есть метод get_perimeter."""
    check_method_perimeter(figure)
    return figure.get_perimeter()
