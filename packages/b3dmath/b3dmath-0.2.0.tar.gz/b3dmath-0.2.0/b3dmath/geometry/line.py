import math
import numpy as np


def line_equation(p0: np.ndarray, p1: np.ndarray) -> np.ndarray:
    """
    Calculate the line equation from two points

    Args:
        p0 (numpy.ndarray): 2d vector representing point 0
        p1 (numpy.ndarray): 2d vector representing point 1
    Returns:
        numpy.ndarray: Line equation coefficients [a, b, c] for ax + by + c = 0
    """
    x0, y0 = p0
    x1, y1 = p1
    a = y1 - y0
    b = x0 - x1
    c = x1 * y0 - x0 * y1
    return np.array([a, b, c])


def sign(line_coefficients: np.ndarray, point: np.ndarray) -> int:
    """
    Calculate the sign of a point relative to a line

    Args:
        line_coefficients (numpy.ndarray): Line equation coefficients [a, b, c] for ax + by + c = 0
        point (numpy.ndarray): 2d vector representing the point
    Returns:
        int: 1 if the point is above the line, -1 if it is below, 0 if it is on the line
    """
    a, b, c = line_coefficients
    x, y = point
    value = a * x + b * y + c
    return np.sign(value)


def closest_point_on_line(position, v0, v1):
    """
    Find the closest point on a line to a position

    Args:
        position (np.ndarray): The position
        v0 (np.ndarray): The first position of the line
        v1 (np.ndarray): The second position of the line
    Returns:
        np.ndarray: The closest point on the line
    """
    # See: https://stackoverflow.com/questions/47481774/getting-point-on-line-segment-that-is-closest-to-another-point
    line_direction = v1 - v0
    t = np.dot(position - v0, line_direction) / np.dot(line_direction, line_direction)
    t = np.clip(t, 0.0, 1.0)
    point_on_line = v0 + t * line_direction
    return point_on_line


def distance_to_line(position, v0, v1, euclidean=True):
    """
    Get the distance from a position to a line

    Args:
        position (np.ndarray): The position
        v0 (np.ndarray): The first position of the line
        v1 (np.ndarray): The second position of the line
    Kwargs:
        euclidean (bool): Whether to use euclidean distance or not
    Returns:
        float: The distance
    """
    l2 = np.sum((v1 - v0) ** 2)
    if l2 == 0:
        return np.sum((v1 - v0) ** 2)
    t = max(0, min(1, np.dot(position - v0, v1 - v0) / l2))
    projection = v0 + t * (v1 - v0)
    output = np.sum((position - projection) ** 2)

    if (euclidean):
        output = math.sqrt(output)

    return output
