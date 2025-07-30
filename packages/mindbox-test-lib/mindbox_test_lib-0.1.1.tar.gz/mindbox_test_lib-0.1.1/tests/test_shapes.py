import math
import random

import pytest

from shapes import Circle, Triangle


def test_circle_are_with_negative_radius():
    with pytest.raises(ValueError):
        Circle(-1)


def test_circle_area():
    for _ in range(10):
        radius = random.uniform(0.1, 100)
        circle = Circle(radius)
        expected_area = math.pi * radius ** 2
        assert math.isclose(circle.area(), expected_area, rel_tol=1e-9)


@pytest.mark.parametrize('a,b,c', [
    (1, 2, 3),
    (1, 10, 20),
    (0, 1, 1),
    (-1, 2, 2),
])
def test_triangle_with_invalid_sides(a, b, c):
    with pytest.raises(ValueError):
        Triangle(a, b, c)


@pytest.mark.parametrize('a,b,c,expected', [
    (5, 12, 13, True),
    (6, 8, 10, True),
    (7, 24, 25, True),
    (1, 1, 1, False),
    (2, 2, 3, False),
])
def test_is_right_triangle(a, b, c, expected):
    tri = Triangle(a, b, c)
    assert tri.is_right() == expected


def test_triangle_square():
    for _ in range(10):
        a, b = random.uniform(0.1, 100), random.uniform(0.1, 100)
        lower, upper = abs(a - b) + 0.001, a + b - 0.001
        if lower >= upper:
            continue
        c = random.uniform(lower, upper)
        triangle = Triangle(a, b, c)
        s = (a + b + c) / 2
        expected_area = math.sqrt(s * (s - a) * (s - b) * (s - c))
        assert math.isclose(triangle.area(), expected_area, rel_tol=1e-9)
