from abc import ABC, abstractmethod
from math import pi

from .utils import add_property
from .validation import check_non_negative_number, check_existing_triangle


class Figure(ABC):
    """Абстрактный класс фигур."""

    @abstractmethod
    def get_perimeter(self) -> int | float:
        """Метод получения периметра фигуры."""
        pass

    @abstractmethod
    def get_square(self) -> float:
        """Метод получения площади фигуры."""
        pass


@add_property
class Circle(Figure):
    """Круг."""

    def __init__(self, radius: int | float):
        check_non_negative_number(radius)
        self.radius = radius

    def get_perimeter(self) -> int | float:
        """Вернет длину окружности круга."""
        return 2 * pi * self.radius

    def get_square(self) -> float:
        """Вернет площадь круга."""
        return pi * self.radius ** 2


@add_property
class Triangle(Figure):

    def __init__(self, a: int | float, b: int | float, c: int | float):
        check_non_negative_number(a, b, c)
        check_existing_triangle(a, b, c)
        self.a, self.b, self.c = a, b, c

    def get_perimeter(self) -> int | float:
        """Вернет периметр треугольника."""
        return self.a + self.b + self.c

    def get_square(self) -> float:
        """
        Вернет площадь треугольника.
        Формула Герона Александрийского.
        """
        p = self.get_perimeter() / 2
        return (p * (p - self.a) * (p - self.b) * (p - self.c)) ** 0.5

    def check_is_rectangular(self) -> bool:
        """
        Вернет True, если треугольник прямоугольный,
        в противном случае - False.
        """
        a, b, c = sorted((self.a, self.b, self.c))
        return bool(a) and a ** 2 + b ** 2 == c ** 2
