import pytest

from square_figures_library import Triangle
from square_figures_library.app.constants import (
    NON_NUMERIC_ERROR,
    NOT_EXISTING_TRIANGLE,
)


class TestTriangle:
    """Проверяет класс Triangle."""

    @pytest.mark.parametrize(
        'sides, expected_square',
        [
            ((1, 1, 1), 0.4330127018922193),
            ((0, 0, 0), 0),
            ((4, 4, 8), 0),
            ((3, 4, 5), 6),
            ((0.001, 0.002, 0.002), 0.0000009682458365518544),
            ((24.15, 16.99, 17.4), 147.7987920405306),
            ((999.0, 777, 444), 165303.56130464945),
        ],
    )
    def test_getting_square(self, sides, expected_square):
        """Получение площади при валидных радиусах."""
        triangle = Triangle(*sides)
        assert triangle.get_square() == expected_square
        assert triangle.square == expected_square

    @pytest.mark.parametrize(
        'sides, expected_perimeter',
        [
            ((1, 1, 1), 3),
            ((0, 0, 0), 0),
            ((4, 4, 8), 16),
            ((3, 4, 5), 12),
            ((0.001, 0.002, 0.002), 0.005),
            ((24.15, 16.99, 17.4), 58.54),
            ((999.0, 777, 444), 2220.0),
        ],
    )
    def test_getting_perimeter(self, sides, expected_perimeter):
        """Получение периметра при валидных радиусах."""
        triangle = Triangle(*sides)
        assert triangle.get_perimeter() == expected_perimeter
        assert triangle.perimeter == expected_perimeter

    @pytest.mark.parametrize(
        'sides, result',
        [
            ((3, 4, 5), True),
            ((22.46584, 37.54578, 43.75385197572895), True),
            ((0, 0, 0), False),
            ((6, 9, 12), False),
        ],
    )
    def test_check_is_rectangular(self, sides, result):
        """
        Проверка метода, проверяющего, является ли треугольник прямоугольным.
        """
        triangle = Triangle(*sides)
        assert triangle.check_is_rectangular() is result

    @pytest.mark.parametrize(
        'bad_side',
        [
            -42,
            -4.2,
            '42',
            [42],
        ],
    )
    def test_non_valid_side(self, bad_side):
        """Проверка на ошибку с невалидными сторонами."""
        sides = (3, 4, 5)
        for i in range(3):
            bad_sides = [
                side if not i == j else bad_side
                for j, side in enumerate(sides)
            ]
            with pytest.raises(ValueError, match=NON_NUMERIC_ERROR):
                _ = Triangle(*bad_sides)

    @pytest.mark.parametrize(
        'bad_sides',
        [
            (4, 4, 9),
            (0, 0, 11),
            (1.001, 0.1101, 10.11),
        ],
    )
    def test_not_existing_triangle(self, bad_sides):
        """
        Проверка на ошибку с валидными данными,
        но не существующим треугольником.
        """
        with pytest.raises(ValueError, match=NOT_EXISTING_TRIANGLE):
            _ = Triangle(*bad_sides)
