import numpy as np


def line_plane_intersect(
    plane_normal: np.ndarray,
    plane_point: np.ndarray,
    line_vector: np.ndarray,
    line_point: np.ndarray
) -> np.ndarray:
    """
    Calculate the intersection point between a line and a plane

    Args:
        plane_normal (numpy.ndarray): The normal vector of the plane
        plane_point (numpy.ndarray): A point on the plane
        line_vector (numpy.ndarray): The direction vector of the line
        line_point (numpy.ndarray): A point on the line
    Returns:
        numpy.ndarray: The intersection point
    """
    denom = np.dot(line_vector, plane_normal)
    if np.isclose(denom, 0):
        return np.full(3, np.nan)
    numerator = np.dot(plane_point - line_point, plane_normal)
    t = numerator / denom
    return line_point + t * line_vector


def are_points_planar(points: np.typing.ArrayLike, eps: float = 0.1) -> bool:
    """
    Check if a set of points are planar (lie flat on a plane)

    Args:
        points (np.typing.ArrayLike): An array of points in 3D space
    Kwargs:
        eps (float, optional): Epsilon for determining planarity.
    Returns:
        bool: True if the points are planar
    """
    points_array = points - np.mean(points, axis=0)
    _, s, _ = np.linalg.svd(points_array)
    return s[-1] < eps
