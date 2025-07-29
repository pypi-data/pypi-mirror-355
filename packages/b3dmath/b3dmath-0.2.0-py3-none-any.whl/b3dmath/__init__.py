"""
Math based helper functions
"""
import math
import numpy as np
import sys


def safe_div(x, y):
    """
    Safely divides two numbers.

    Args:
        x (float): The numerator.
        y (float): The denominator.

    Returns:
        float: The division result.
    """
    return x / (y if y != 0.0 else 0.0001)


def lerp(a, b, x):
    """
    Linearly interpolates between two values.

    Args:
        a (number): The lower value to interpolate from.
        b (number): The higher value to interpolate to.
        x (number): The alpha value to interpolate with.

    Returns:
        float: The interpolated value.
    """
    return (a * (1.0 - x)) + (b * x)


def remap(value, start, stop, target_start, target_stop):
    """
    Remaps a value from [start..stop] to [target_start..target_stop]

    Args:
        value (number): The value to remap
        start (number): The existing start value
        stop (number): The existing stop value
        target_start (number): The target start value
        target_stop (number): The target stop value

    Returns:
        number: The number remapped
    """
    return np.interp(value, [start, stop], [target_start, target_stop])
    # return target_start + (target_stop - target_start) * safe_div((value - start), (stop - start))


def is_power_of_2(n):
    """
    Checks if an integer is a power of two number.

    Args:
        n (int): The integer to check.

    Returns:
        bool: True if the input is power of two - else False.
    """
    return n > 0 and (n & (n - 1)) == 0


def round_integer_up_to_power_of_two(input_int):
    """
    Rounds up an input integer to the nearest power of two.

    Args:
        input_int (int): The integer to round up.

    Returns:
        int: The integer rounded up to the nearest power of two.
    """
    return 2 ** math.ceil(math.log2(input_int))


if sys.version_info.minor >= 8:
    from math import prod
    from math import factorial

else:
    def prod(v) -> int:
        """
        Given a list of numbers, this will return the product of all of them.

        Args:
            v (list): The list of numbers to multiply together.
        Returns:
            int: The product of all the numbers.
        """
        output = 1
        for i in v:
            output *= i
        return output

    def factorial(n):
        """
        Given a number, this will return the factorial of it.

        Args:
            n (int): The number to get the factorial of.
        Returns:
            int: The factorial of the number.
        """
        return prod([x for x in range(1, n + 1)])
