import numpy as np


def are_vertices_spherical(vertices, deviation=0.0):
    """
    Checks if input vertices can generate a spherical mesh.
    (A mesh where all vertices lie on the surface of a sphere)

    Args:
        vertices (np.typing.ArrayLike): The vertices to check
    Kwargs:
        deviation (float): Deviation allowed in the distance calculation,
            E.g. 0.05 means that the distance of each vertex from the center
            can deviate by 5% of the average distance of all vertices from the center.
    Returns:
        bool: True if the vertices are spherical - else False
    """
    if np.all(vertices == 0):
        return False

    center = np.mean(vertices, axis=0)
    distances = np.linalg.norm(vertices - center, axis=1)
    if not np.allclose(distances, distances[0], atol=(distances[0] * deviation)):
        return False
    return True
