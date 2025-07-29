import numpy as np
import typing


def triangle_numbers(upper) -> typing.Generator[int, None, None]:
    """
    Generate triangle numbers

    Args:
        upper (int): Upper limit of triangle numbers to generate
    Yields:
        int: Next triangle number
    """
    for i in range(1, upper):
        # yield sum([x for x in range(1, i)])
        yield i * (i + 1) // 2  # sum of arithmetic series


def pascals_triangle(n) -> list:
    """
    Generate the first n rows of Pascal's triangle

    Args:
        n (int): Number of rows to generate
    Returns:
        list: List of lists of the rows
    """
    output = [[1]]
    for i in range(1, n):
        output.append([1])
        for j in range(1, i):
            output[i].append(output[i - 1][j - 1] + output[i - 1][j])
        output[i].append(1)
    return output


def cumcount(arr: np.ndarray) -> np.ndarray:
    """
    Calculates the cumulative count at each index in a 1D array

    E.g. np.array([1, 3, 3, 5, 6, 2, 1, 2, 2]) -> np.array([1, 1, 2, 1, 1, 1, 2, 2, 3])

    Args:
        arr (np.ndarray): The 1D array to calculate cumulative counts for
    Returns:
        np.ndarray: The calculated cumulative counts as a 1D array
    """
    output = np.zeros(arr.shape, dtype=arr.dtype)
    value_counts = {}
    for i in range(len(arr)):
        value = str(arr[i])
        if value not in value_counts:
            value_counts[value] = np.int64(0)
        count = value_counts[value]
        output[i] = count
        value_counts[value] = count + 1
    return output + 1
