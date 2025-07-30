from typing import Protocol


class FiguresProtocol(Protocol):
    """Протокол для фигур."""

    def get_perimeter(self) -> int | float:
        """Метод получения периметра фигуры."""
        pass

    def get_square(self) -> float:
        """Метод получения площади фигуры."""
        pass
