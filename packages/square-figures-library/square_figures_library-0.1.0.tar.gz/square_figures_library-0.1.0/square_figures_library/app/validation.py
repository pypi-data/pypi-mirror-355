from .constants import NON_NUMERIC_ERROR, NOT_EXISTING_TRIANGLE, NOT_METHOD
from .protocol import FiguresProtocol


def check_method_square(figure: FiguresProtocol) -> None:
    """Проверка на наличие метода get_square у класса."""
    get_square = 'get_square'
    if not hasattr(figure, get_square):
        raise AttributeError(NOT_METHOD.format(get_square))


def check_method_perimeter(figure: FiguresProtocol) -> None:
    """Проверка на наличие метода get_perimeter у класса."""
    get_perimeter = 'get_perimeter'
    if not hasattr(figure, get_perimeter):
        raise AttributeError(NOT_METHOD.format(get_perimeter))


def check_non_negative_number(*args) -> None:
    if not (
        all((isinstance(arg, (int, float)) for arg in args))
        and all((i >= 0 for i in args))
    ):
        raise ValueError(NON_NUMERIC_ERROR)


def check_existing_triangle(
    a: int | float, b: int | float, c: int | float,
) -> None:
    """Проверит, возможен ли треугольник с данными сторонами."""
    if not (a + b >= c and a + c >= b and b + c >= a):
        raise ValueError(NOT_EXISTING_TRIANGLE)
