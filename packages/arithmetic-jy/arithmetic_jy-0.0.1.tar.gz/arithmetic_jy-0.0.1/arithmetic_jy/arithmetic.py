import numpy as np


def add(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Add two arrays element-wise.

    Args:
        a: First array.
        b: Second array.

    Returns:
        Result of adding `a` and `b` element-wise.

    """
    return a + b

def subtract(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Subtract two arrays element-wise.

    Args:
        a: First array.
        b: Second array.

    Returns:
        Result of subtracting `b` from `a` element-wise.

    """
    return a - b

def multiply(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Multiply two arrays element-wise.

    Args:
        a: First array.
        b: Second array.

    Returns:
        Result of multiplying `a` and `b` element-wise.

    """
    return a * b

def divide(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Divide two arrays element-wise.

    Args:
        a: First array.
        b: Second array.

    Returns:
        Result of dividing `a` by `b` element-wise.

    """
    if np.any(b == 0):
        raise ValueError("Division by zero encountered in array 'b'.")
    return a / b