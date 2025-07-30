import pytest

from square_figures_library import calculate_perimeter, calculate_square


class TestUtils:
    """Проверяет работу функций-утилит."""

    @pytest.mark.parametrize(
        'size',
        [
            0,
            1,
            0.5,
            10.25,
        ],
    )
    def test_calculate_perimeter(self, data_magic_figure, size):
        """Проверит работу calculate_perimeter."""
        magic_figure, magic_perimeter, _ = data_magic_figure(size)
        assert calculate_perimeter(magic_figure) == magic_perimeter

    @pytest.mark.parametrize(
        'size',
        [
            0,
            1,
            0.5,
            10.25,
        ],
    )
    def test_calculate_square(self, data_magic_figure, size):
        """Проверит работу calculate_square."""
        magic_figure, _, magic_square = data_magic_figure(size)
        assert calculate_square(magic_figure) == magic_square
