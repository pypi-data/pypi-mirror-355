def data_row_exists(contents, new_row, column=0):
    """
    Check if the specified column of `new_row` matches the same column of any row in `contents`.

    Parameters:
        new_row (list): A list representing the row to check.
        contents (list of lists): The existing rows to search within, where each row is a list.
        column (int, optional): The index of the column to compare. Defaults to 0.

    Returns:
        tuple: (exists, index, matched_row)
            exists (bool): True if a matching value is found in the specified column, else False.
            index (int or None): The index of the matching row in `contents` if found, else None.
            matched_row (list or None): The matched row from `contents` if found, else None.

    Notes:
        - Matching is based on the value in the specified column.
        - Assumes `new_row` and each row in `contents` have enough columns to access the specified index.
        - Raises IndexError if `column` is out of range for any row.
    """
    key = new_row[column]
    for i, row in enumerate(contents):
        if row and row[column] == key:
            return True, i, row
    return False, None, None

def data_exact_row_exists(contents, new_row, case_sensitive=False, type_sensitive=False):
    """
    Check if a fully identical row exists in `contents`, with options for case and type sensitivity.

    Parameters:
        new_row (list): A list representing the row to check.
        contents (list of lists): The existing rows to search within, where each row is a list.
        case_sensitive (bool, optional): If True, string comparisons are case-sensitive. Defaults to False.
        type_sensitive (bool, optional): If True, type mismatches cause non-match. Defaults to False.

    Returns:
        tuple: (exists, matched_indices)
            exists (bool): True if one or more matches are found based on the given sensitivity options.
            matched_indices (list): A list of indices in `contents` where rows match `new_row` based on sensitivity.

    Notes:
        - Matching requires the same number of elements in each row.
        - If `case_sensitive` is False, string comparisons are case-insensitive.
        - If `type_sensitive` is False, values with equal string representations are considered equal.
    """


    matched_indices = [i for i, row in enumerate(contents) if data_rows_match(row, new_row, case_sensitive==case_sensitive, type_sensitive=type_sensitive)]
    exists = len(matched_indices) > 0
    return exists, matched_indices

def data_rows_match(row1, row2, case_sensitive=False, type_sensitive=False):
    """
    Compares two rows (lists, tuples, etc.) element-wise to determine if they match.

    Parameters:
        row1 (iterable): The first row to compare.
        row2 (iterable): The second row to compare.
        case_sensitive (bool): If True, string comparisons are case-sensitive.
                               If False (default), strings are compared case-insensitively.
        type_sensitive (bool): If True, values are compared with type sensitivity (e.g., 1 != "1").
                               If False (default), values are converted to strings before comparison.

    Returns:
        bool: True if the rows match element-wise according to the specified sensitivity flags,
              False otherwise.
    """
    if len(row1) != len(row2):
        return False
    for v1, v2 in zip(row1, row2):
        if type_sensitive:
            if v1 != v2:
                return False
        else:
            s1, s2 = str(v1), str(v2)
            if case_sensitive:
                if s1 != s2:
                    return False
            else:
                if s1.lower() != s2.lower():
                    return False
    return True

def data_remove_rows(contents, indices):
    """
    Remove multiple rows from contents based on a list of indices.

    Parameters:
        contents (list of lists): The CSV data as a list of rows.
        indices (list or set of int): Indices of rows to remove.

    Returns:
        list: New list with specified rows removed.

    Notes:
        - Indices that are out of range are ignored.
        - The order of remaining rows is preserved.
    """
    indices_set = set(indices)  # For faster lookup
    return [row for i, row in enumerate(contents) if i not in indices_set]

