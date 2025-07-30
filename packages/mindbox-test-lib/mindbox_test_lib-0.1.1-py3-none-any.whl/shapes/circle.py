import math

from .interfaces import Shape


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        if radius < 0:
            raise ValueError('Радиус не может быть отрицательным!')
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius ** 2
