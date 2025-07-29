import enum
import numpy as np


class AngleUnits(enum.Enum):
    """
    Enum used to represent the rotation format in degrees
    """
    DEGREES = 0
    RADIANS = 1


def degrees_to_radians(degrees: np.array) -> np.array:
    """
    Converts degrees to radians

    Args:
        degrees (np.array): The degrees to convert

    Returns:
        np.array: The radians
    """
    return degrees * np.pi / 180.0


def vector_to_euler(v: np.array) -> np.array:
    """
    Converts a direction vector to euler angles

    Note: Assumes we're following the above world vectors

    Args:
        v (np.array): The xyz direction vector
    Returns:
        np.array: The euler ypr euler angles (in radians)
    """
    x, y, z = v
    yaw = np.arctan2(x, y)
    pitch = np.arctan2(np.sqrt(x**2 + y**2), z)
    roll = 0.0

    out = np.array([yaw, pitch, roll])
    return out
