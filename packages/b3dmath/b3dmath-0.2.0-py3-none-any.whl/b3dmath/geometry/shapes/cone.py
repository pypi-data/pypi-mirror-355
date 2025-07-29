import math
import numpy as np

import b3dmath.algebra


def line_cone_intersect(
    line_pos: np.ndarray, line_dir: np.ndarray,
    cone_pos: np.ndarray, cone_dir: np.ndarray,
    cone_angle: float
) -> tuple[np.ndarray, np.ndarray] | None:
    """
    Finds the intersection between a line and a cone

    Based on: https://www.shadertoy.com/view/MtcXWr

    Args:
        line_pos (np.ndarray): The position of the line
        line_dir (np.ndarray): The direction of the line
        cone_pos (np.ndarray): The position of the cone
        cone_dir (np.ndarray): The direction of the cone
        cone_angle (float): The angle of the cone (in degrees)

    Returns:
        Tuple[Vector3, Vector3]: The two points of intersection
    """
    cone_angle = math.radians(cone_angle) / 2

    # Coefficients
    co = line_pos - cone_pos
    a = np.dot(line_dir, cone_dir) * np.dot(line_dir, cone_dir) - math.cos(cone_angle) * math.cos(cone_angle)

    b = 2.0 * (
        np.dot(line_dir, cone_dir) * np.dot(co, cone_dir) -
        np.dot(line_dir, co) * math.cos(cone_angle) * math.cos(cone_angle)
    )
    c = np.dot(co, cone_dir) * np.dot(co, cone_dir) - np.dot(co, co) * math.cos(cone_angle) * math.cos(cone_angle)

    # Solve quadratic
    t1, t2 = b3dmath.algebra.solve_quadratic(a, b, c)

    # Find the closest intersection
    t = t1
    if (t < 0.0):
        return None

    # cp = line_pos + t * line_dir - cone_pos
    # n = cp * np.dot(cone_dir, cp) / np.dot(cp, cp) - cone_dir
    # n = n / np.linalg.norm(n)

    return (line_pos + t * line_dir, line_pos + t2 * line_dir)


def is_point_in_cone(point: np.ndarray, cone_pos: np.ndarray, cone_dir: np.ndarray, cone_angle: float) -> bool:
    """
    Checks if a point is inside a cone

    Args:
        point (np.ndarray): The point to check
        cone_pos (np.ndarray): The position of the cone
        cone_dir (np.ndarray): The direction of the cone
        cone_angle (float): The angle of the cone (in degrees)

    Returns:
        bool: Whether the point is inside the cone
    """
    cone_angle = math.radians(cone_angle) / 2

    cp = point - cone_pos
    return np.dot(cp, cone_dir) >= np.linalg.norm(cp) * math.cos(cone_angle)
