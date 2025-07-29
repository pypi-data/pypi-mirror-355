import numpy as np


def are_vertices_cuboidal(verts: np.ndarray, deviation=0.0):
    """
    Checks if 8 input vertices can generate a cuboidal mesh

    Args:
        vertices (numpy.typing.ArrayLike): The vertices to check
    Kwargs:
        deviation (float): Percent of deviation allowed in the distance calculation
            (as an 0..1 percentage of the radius).
            Defaults to 0.0.
    Returns:
        bool: True if the vertices are cuboidal - else False
    """
    if np.all(verts == 0):
        return False

    if verts.shape != (8, 3):
        raise ValueError("Input must be an array of shape (8, 3) representing 8 vertices in 3D space.")

    center = np.mean(verts, axis=0)

    directions = verts - center

    # All verts should be equidistant from the center
    distances = np.linalg.norm(directions, axis=1)
    if not np.allclose(distances, distances[0], atol=(distances[0] * deviation)):
        return False

    # A cube only has 3 unique directions vectors (ignoring sign)
    inverted_directions = directions * -1.0
    for i, dir_ in enumerate(directions):
        found = False
        for j, inv_dir in enumerate(inverted_directions):
            if i == j:
                continue
            elif np.allclose(dir_, inv_dir, atol=0.05):
                found = True
                break
        if not found:
            return False

    return True
