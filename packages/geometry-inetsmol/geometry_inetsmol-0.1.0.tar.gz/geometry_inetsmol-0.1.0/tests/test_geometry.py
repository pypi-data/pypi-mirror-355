from geometry-inetsmol import Circle, Triangle
from geometry-inetsmol.factory import shape_from_args

def test_circle_area():
    assert round(Circle(1).area(), 5) == round(3.14159, 5)

def test_triangle_area():
    t = Triangle(3, 4, 5)
    assert round(t.area(), 2) == 6.0

def test_triangle_right():
    assert Triangle(3, 4, 5).is_right() is True
    assert Triangle(3, 4, 6).is_right() is False

def test_shape_factory_circle():
    s = shape_from_args(2)
    assert round(s.area(), 2) == round(3.14159 * 4, 2)

def test_shape_factory_triangle():
    s = shape_from_args(3, 4, 5)
    assert round(s.area(), 2) == 6.0
