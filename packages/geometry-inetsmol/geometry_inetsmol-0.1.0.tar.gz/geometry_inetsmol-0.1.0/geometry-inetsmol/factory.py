from geometry import Circle, Triangle, Shape

def shape_from_args(*args: float) -> Shape:
    if len(args) == 1:
        return Circle(args[0])
    elif len(args) == 3:
        return Triangle(*args)
    raise ValueError("Unsupported shape arguments")
