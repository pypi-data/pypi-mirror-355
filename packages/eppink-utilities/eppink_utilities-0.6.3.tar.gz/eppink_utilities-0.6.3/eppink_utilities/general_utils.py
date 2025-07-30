import numpy as np
import ast
import os

def validate_inputs(*args, dtype=float, allow_scalar=True, check_broadcast=True):
    """
    Validates and converts inputs to NumPy arrays of the specified dtype,
    ensuring that np.nan values are preserved if dtype supports them.

    Parameters:
        *args: Variable length argument list of inputs to be validated and converted.
        dtype: Desired data type of the output arrays (default: float).
        allow_scalar (bool): If False, scalar inputs will raise a ValueError.
        check_broadcast (bool): If True, checks that all inputs can be broadcast together.

    Returns:
        Each validated input as a separate NumPy array (not packed in a tuple).

    Raises:
        TypeError: If any input cannot be converted to the specified dtype.
        ValueError: If scalar inputs are disallowed but found,
                    or if inputs cannot be broadcast together,
                    or if nan values are present but dtype is integer.
    """
    arrays = []
    for arg in args:
        arr_raw = np.asarray(arg)  # no dtype yet, preserves nans
        if np.any(np.isnan(arr_raw)):
            # Check if dtype supports nan:
            if np.issubdtype(dtype, np.integer):
                raise ValueError(f"Input {arg} contains NaN but dtype={dtype} does not support NaN.")
            # else dtype supports nan, proceed

        try:
            arr = np.asarray(arg, dtype=dtype)
        except Exception as e:
            raise TypeError(f"Input {arg} cannot be converted to array of type {dtype}") from e

        if not allow_scalar and arr.ndim == 0:
            raise ValueError(f"Scalar input {arg} not allowed.")

        arrays.append(arr)

    if check_broadcast:
        try:
            np.broadcast(*arrays)
        except ValueError as e:
            raise ValueError("Inputs are not broadcast-compatible.") from e

    return (*arrays,)

def extract_functions_with_docstrings(file_path):
    """
    Parses a Python file and extracts all top-level function names and their docstrings.

    Parameters:
        file_path (str): Path to the Python source file.

    Returns:
        list of tuple: A list of (function_name, docstring) tuples.
                       If a function has no docstring, a placeholder message is used.
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        source = f.read()

    tree = ast.parse(source)
    functions = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            func_name = node.name
            docstring = ast.get_docstring(node)
            functions.append((func_name, docstring or "No description provided."))

    return functions

def list_py_files(directory: str) -> list:
    """
    List all Python files in a directory, excluding '__init__.py'.

    Parameters:
        directory (str): Path to the directory to scan.

    Returns:
        list of str: List of .py file paths.
    """
    py_files = []
    for file in os.listdir(directory):
        if file.endswith(".py") and file != "__init__.py":
            py_files.append(os.path.join(directory, file))
    return py_files