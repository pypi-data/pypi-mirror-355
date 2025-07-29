import numpy as np


def solve_quadratic(a, b, c):
    """
    Solves the quadratic equation
    Returns a tuple of the two solutions.

    Args:
        a (float): The coefficient of x^2
        b (float): The coefficient of x
        c (float): The constant
    Returns:
        Tuple[float, float]: The two solutions
    """
    det = b * b - 4 * a * c
    if det < 0:
        return None
    det = np.sqrt(det)
    t0 = (-b - det) / (2 * a)
    t1 = (-b + det) / (2 * a)
    return t0, t1
