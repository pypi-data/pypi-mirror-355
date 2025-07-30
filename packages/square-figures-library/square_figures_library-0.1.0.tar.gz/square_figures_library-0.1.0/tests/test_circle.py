import pytest

from square_figures_library import Circle
from square_figures_library.app.constants import NON_NUMERIC_ERROR


class TestCircle:
    """Проверяет класс Circle."""

    @pytest.mark.parametrize(
        'radius, expected_square',
        [
            (1, 3.141592653589793),
            (0, 0),
            (10, 314.1592653589793),
            (0.001, 0.000003141592653589793),
            (24.15, 1832.247521408273),
            (999.0, 3135312.609875267),
        ],
    )
    def test_getting_square(self, radius, expected_square):
        """Получение площади при валидных радиусах."""
        circle = Circle(radius)
        assert circle.get_square() == expected_square
        assert circle.square == expected_square

    @pytest.mark.parametrize(
        'radius, expected_perimeter',
        [
            (1, 6.283185307179586),
            (0, 0),
            (10, 62.83185307179586),
            (0.001, 0.006283185307179587),
            (24.15, 151.738925168387),
            (999.0, 6276.9021218724065),
        ],
    )
    def test_getting_perimeter(self, radius, expected_perimeter):
        """Получение периметра при валидных радиусах."""
        circle = Circle(radius)
        assert circle.get_perimeter() == expected_perimeter
        assert circle.perimeter == expected_perimeter

    @pytest.mark.parametrize(
        'radius',
        [
            -42,
            -4.2,
            '42',
            [42],
        ],
    )
    def test_non_valid_radius(self, radius):
        """Проверка на ошибку с невалидным радиусом."""
        with pytest.raises(ValueError, match=NON_NUMERIC_ERROR):
            _ = Circle(radius)
