import math
import numpy as np

import b3dmath.math.geometry.coordinates
import b3dmath.math.geometry.line


def closest_point_on_tri(position, v0, v1, v2):
    """
    Get the closest point on a triangle to a position

    Args:
        position (np.ndarray): The position
        v0 (np.ndarray): The first position of the triangle
        v1 (np.ndarray): The second position of the triangle
        v2 (np.ndarray): The third position of the triangle
    Returns:
        np.ndarray: The closest point on the triangle
    """
    tri_normal = np.cross(v1 - v0, v2 - v0)
    tri_normal = tri_normal / np.linalg.norm(tri_normal)

    # project pos onto the plane of the triangle
    d = np.dot(tri_normal, v0 - position)
    projected_pos = position + d * tri_normal

    # if the point is inside the triangle then return the pos
    e0, e1, e2 = (v1 - v0, v2 - v1, v0 - v2)
    c0, c1, c2 = (projected_pos - v0, projected_pos - v1, projected_pos - v2)

    if (
        np.dot(np.cross(e0, c0), tri_normal) > 0 and
        np.dot(np.cross(e1, c1), tri_normal) > 0 and
        np.dot(np.cross(e2, c2), tri_normal) > 0
    ):
        return projected_pos

    # else find the closest point on an edge
    d0 = b3dmath.math.geometry.line.distance_to_edge(projected_pos, v0, v1, euclidean=False)
    d1 = b3dmath.math.geometry.line.distance_to_edge(projected_pos, v1, v2, euclidean=False)
    d2 = b3dmath.math.geometry.line.distance_to_edge(projected_pos, v2, v0, euclidean=False)

    check_verts = []

    if (d0 < d1 and d0 < d2):
        check_verts = [v0, v1]
    elif (d1 < d0 and d1 < d2):
        check_verts = [v1, v2]
    else:
        check_verts = [v2, v0]

    return b3dmath.math.geometry.line.closest_point_lying_on_edge(
        projected_pos,
        check_verts[0],
        check_verts[1]
    )


def is_point_inside_tri(position, v0, v1, v2):
    """
    Check if a point is inside a triangle

    Args:
        position (np.ndarray): The position
        v0 (np.ndarray): The first position of the triangle
        v1 (np.ndarray): The second position of the triangle
        v2 (np.ndarray): The third position of the triangle
    Returns:
        bool: True if the point is inside the triangle - else False
    """
    u, v, w = b3dmath.math.geometry.coordinates.calculate_barycenter(
        v0, v1, v2, position
    )
    return np.all(u >= 0) and np.all(v >= 0) and np.all(w >= 0)


def get_distance_to_tri(position, v0, v1, v2, euclidean=True):
    """
    Get the minimum distance from a position to a triangle

    Args:
        position (np.ndarray): The position
        v0 (np.ndarray): The first position of the triangle
        v1 (np.ndarray): The second position of the triangle
        v2 (np.ndarray): The third position of the triangle
    Kwargs:
        euclidean (bool): Whether to use euclidean distance or not
    Returns:
        float: The distance
    """
    closest_point = closest_point_on_tri(position, v0, v1, v2)
    output = np.sum((position - closest_point) ** 2)

    if (euclidean):
        output = math.sqrt(output)

    return output
