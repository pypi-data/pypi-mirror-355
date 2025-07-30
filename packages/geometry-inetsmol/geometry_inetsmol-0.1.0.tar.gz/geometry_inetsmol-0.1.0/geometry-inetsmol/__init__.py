from abc import ABC, abstractmethod
from math import pi, sqrt, isclose

class Shape(ABC):
    @abstractmethod
    def area(self) -> float:
        pass

class Circle(Shape):
    def __init__(self, radius: float):
        self.r = radius

    def area(self) -> float:
        return pi * self.r ** 2

class Triangle(Shape):
    def __init__(self, a: float, b: float, c: float):
        self.a, self.b, self.c = sorted([a, b, c])

    def area(self) -> float:
        p = (self.a + self.b + self.c) / 2
        return sqrt(p * (p - self.a) * (p - self.b) * (p - self.c))

    def is_right(self) -> bool:
        return isclose(self.a**2 + self.b**2, self.c**2)
