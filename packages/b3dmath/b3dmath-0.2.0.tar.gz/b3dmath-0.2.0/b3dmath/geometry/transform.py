import numpy as np
import typing
from scipy.spatial.transform import Rotation as R

import b3dmath.math.geometry.angles
from b3dmath.math.geometry.angles import AngleUnits


def compose_prs_matrices(
    position_matrix: np.matrix,
    rotation_matrix: np.matrix,
    scale_matrix: np.matrix,
    angle_units=AngleUnits.DEGREES
) -> np.array:
    """
    Composes a position, rotation and scale matrix into a single transform matrix

    Args:
        position_matrix (np.matrix): The position matrix
        rotation_matrix (np.matrix): The rotation matrix
        scale_matrix (np.matrix): The scale matrix
    Kwargs:
        angle_units (AngleUnits): The angle units of the rotation matrix
            (default is AngleUnits.DEGREES)
    Returns:
        np.array: The composed transform matrix
    """
    if angle_units == AngleUnits.DEGREES:
        rotation_matrix_deg = np.copy(rotation_matrix)
        rotation_matrix = b3dmath.math.geometry.angles.degrees_to_radians(rotation_matrix_deg)
    transform = position_matrix @ rotation_matrix @ scale_matrix
    return transform


def compose_prs(
    position: np.array,
    rotation: np.array,
    scale: np.array,
    angle_units=AngleUnits.DEGREES
) -> np.array:
    """
    Composes a position, rotation and scale into a single transform matrix

    Args:
        position (np.array): The position
        rotation (np.array): The rotation
        scale (np.array): The scale
    Kwargs:
        angle_units (AngleUnits): The angle units of the rotation matrix
            (default is AngleUnits.DEGREES)
    Returns:
        np.array: The composed transform matrix
    """
    position_matrix = np.eye(4)
    position_matrix[0:3, 3] = position

    rotation_matrix = R.from_euler('xyz', rotation, degrees=True).as_matrix()

    scale_matrix = np.eye(4)
    scale_matrix[0:3, 0:3] = np.diag(scale)

    return compose_prs_matrices(position_matrix, rotation_matrix, scale_matrix, angle_units)


def decompose_prs_matrix(matrix: np.array) -> typing.Tuple[np.array, np.array, np.array]:
    """
    Decomposes a transform matrix into a position, rotation and scale

    Note: Does not handle shear / skew

    Args:
        matrix (np.array): The transform matrix
    Returns:
        typing.Tuple[np.array, np.array, np.array]: The position, rotation and scale
    """
    position = matrix[0:3, 3]

    rotation_matrix = matrix[0:3, 0:3]
    rotation_matrix = rotation_matrix / np.linalg.norm(rotation_matrix, axis=0)
    rotation = R.from_matrix(rotation_matrix).as_euler('xyz', degrees=True)

    scale = np.array([
        np.linalg.norm(matrix[0:3, 0]),
        np.linalg.norm(matrix[0:3, 1]),
        np.linalg.norm(matrix[0:3, 2])
    ])

    return position, rotation, scale
