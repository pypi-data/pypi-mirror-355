import numpy as np


def pos_from_barycentric_coords(
    v0: np.ndarray,
    v1: np.ndarray,
    v2: np.ndarray,
    uv: np.ndarray
) -> np.ndarray:
    """
    Get a position from barycentric coordinates

    Args:
        v0 (np.ndarray): The first position
        v1 (np.ndarray): The second position
        v2 (np.ndarray): The third position
        uv (np.ndarray): The barycentric coordinates

    Returns:
        np.ndarray: The position
    """
    u, v = uv
    return v0 + u * (v1 - v0) + v * (v2 - v0)


def calculate_barycenter(
    v0: np.ndarray, v1: np.ndarray, v2: np.ndarray, pos: np.ndarray
) -> np.ndarray:
    """
    Get barycentric coordinates from a position

    Args:
        v0 (np.ndarray): The first position
        v1 (np.ndarray): The second position
        v2 (np.ndarray): The third position
        pos (np.ndarray): The position

    Returns:
        np.ndarray: The barycentric u, v, w coordinates
    """
    v0v1 = v1 - v0
    v0v2 = v2 - v0
    v0p = pos - v0

    dot00 = np.dot(v0v1, v0v1)
    dot01 = np.dot(v0v1, v0v2)
    dot02 = np.dot(v0v1, v0p)
    dot11 = np.dot(v0v2, v0v2)
    dot12 = np.dot(v0v2, v0p)

    inv_denom = 1 / (dot00 * dot11 - dot01 * dot01)
    u = (dot11 * dot02 - dot01 * dot12) * inv_denom
    v = (dot00 * dot12 - dot01 * dot02) * inv_denom
    w = 1 - u - v

    return np.array([u, v, w])
