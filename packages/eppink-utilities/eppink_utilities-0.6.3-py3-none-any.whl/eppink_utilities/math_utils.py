import numpy as np
from scipy import stats
from scipy.integrate import trapezoid

def average(data, mode='arithmetic', weights=None, window=2, time=None):
    """
    Compute column-wise averages over a 2D data array with multiple modes.
    
    Parameters:
        data (array-like): 2D iterable of shape (n_samples, n_features). May contain np.nan, None, or ''.
        mode (str): Averaging mode. Options:
            - 'arithmetic': Simple mean (default)
            - 'weighted': Weighted average (requires `weights`)
            - 'geometric': Geometric mean
            - 'harmonic': Harmonic mean
            - 'median': Median
            - 'mode': Most frequent value
            - 'moving': Moving average (requires `window`)
            - 'trapezoidal': Integral-based average (requires `time`)
        weights (array-like): Optional. Weights for 'weighted' mode.
        window (int): Window size for 'moving' average.
        time (array-like): Time values for 'trapezoidal' mode.

    Returns:
        numpy.ndarray: 1D or 2D array of averages per column. Missing columns → None; partial NaN → skip; all-NaN → np.nan.
    """
    data = np.asarray(data, dtype=object)

    if data.size == 0:
        return np.array([], dtype=object)

    n_rows, n_cols = data.shape if data.ndim == 2 else (len(data), 1)
    results = []

    if mode == 'moving':
        # Moving average returns 2D output
        moving_results = []
        for col in range(n_cols):
            col_data = np.array([x[col] if isinstance(x, (list, tuple, np.ndarray)) else x for x in data], dtype=object)
            valid = np.array([(x if isinstance(x, (int, float, np.number)) and not np.isnan(x) else np.nan) for x in col_data])
            col_result = []
            for i in range(n_rows - window + 1):
                window_vals = valid[i:i + window]
                if np.all(np.isnan(window_vals)):
                    col_result.append(None)
                else:
                    col_result.append(np.nanmean(window_vals))
            moving_results.append(col_result)
        return np.array(moving_results, dtype=object).T

    for col in range(n_cols):
        column = np.array([row[col] if isinstance(row, (list, tuple, np.ndarray)) else row for row in data], dtype=object)
        valid = np.array([
            x if isinstance(x, (int, float, np.number)) and not isinstance(x, bool) and not (isinstance(x, float) and np.isnan(x)) else np.nan
            for x in column
        ], dtype=float)
        valid_mask = ~np.isnan(valid)
        valid_vals = valid[valid_mask]

        if len(valid_vals) == 0:
            if np.all(np.equal(column, None)) or np.all(column == ''):
                results.append(None)
            else:
                results.append(np.nan)
            continue

        if mode == 'arithmetic':
            results.append(np.nanmean(valid_vals))

        elif mode == 'weighted':
            if weights is None:
                raise ValueError("Weights are required for weighted average.")
            w = np.asarray(weights, dtype=float)
            w = w[valid_mask]
            results.append(np.average(valid_vals, weights=w))

        elif mode == 'geometric':
            results.append(stats.gmean(valid_vals))

        elif mode == 'harmonic':
            results.append(stats.hmean(valid_vals))

        elif mode == 'median':
            results.append(np.nanmedian(valid_vals))

        elif mode == 'mode':
            m = stats.mode(valid_vals, nan_policy='omit')
            results.append(m.mode[0] if len(m.mode) else np.nan)

        elif mode == 'trapezoidal':
            if time is None:
                raise ValueError("Time values are required for trapezoidal average.")
            t = np.asarray(time, dtype=float)
            valid_t = t[valid_mask]
            values = valid_vals
            if len(values) < 2:
                results.append(np.nan)
            else:
                integral = trapezoid(values, x=valid_t)
                duration = valid_t[-1] - valid_t[0]
                results.append(integral / duration if duration != 0 else np.nan)

        else:
            raise ValueError(f"Unsupported averaging mode: {mode}")

    return np.array(results, dtype=object)

def safe_divide(numerator, denominator, warnings=False):
    """
    Safely divide two numbers (scalars, arrays, or combinations thereof),
    avoiding division by zero or invalid operations and propagating NaNs
    from numerator or denominator.

    Parameters:
    ----------
    numerator : float, int, array-like
        The numerator(s) in the division.
    denominator : float, int, array-like
        The denominator(s) in the division.
    warnings: bool
        When True, prints warnings to the terminal

    Returns:
    -------
    result : float or np.ndarray
        The result of the division. Any division by zero or invalid result
        (e.g., inf, -inf, nan) is replaced with np.nan.
        Also, if numerator or denominator is NaN at any position, result is NaN there.

    """
    numerator = np.asarray(numerator, dtype=float)
    denominator = np.asarray(denominator, dtype=float)

    # Detect division by zero positions before division
    zero_div_mask = (denominator == 0)

    with np.errstate(divide='ignore', invalid='ignore'):
        result = np.true_divide(numerator, denominator)

    # Create a mask where numerator or denominator is nan
    nan_mask = np.isnan(numerator) | np.isnan(denominator)

    # Also replace inf, -inf, and nan in result with nan
    invalid_mask = ~np.isfinite(result)

    # Combine masks so that all invalid places are nan
    combined_mask = nan_mask | invalid_mask

    if np.any(zero_div_mask):
        if warnings == True:
            print("Error: Division by zero encountered.")

    if np.isscalar(result):
        if combined_mask:
            return np.nan
        return result

    result[combined_mask] = np.nan

    return result

if __name__ == '__main__':
    import numpy as np
    from pprint import pprint

    test_cases = [
        {
            "name": "All valid data",
            "data": [
                [1.0, 2.0],
                [3.0, 4.0],
                [5.0, 6.0]
            ]
        },
        {
            "name": "Some NaNs",
            "data": [
                [1.0, np.nan],
                [2.0, 4.0],
                [np.nan, 6.0]
            ]
        },
        {
            "name": "All NaNs",
            "data": [
                [np.nan, np.nan],
                [np.nan, np.nan],
                [np.nan, np.nan]
            ]
        },
        {
            "name": "Some missing (None, '')",
            "data": [
                [1.0, ''],
                [2.0, None],
                [3.0, 6.0]
            ]
        },
        {
            "name": "All missing",
            "data": [
                [None, ''],
                [None, ''],
                [None, '']
            ]
        },
        {
            "name": "Empty array",
            "data": []
        }
    ]

    modes = [
        'arithmetic',
        'weighted',
        'geometric',
        'harmonic',
        'median',
        'mode',
        'moving',
        'trapezoidal'
    ]

    weights = [0.1, 0.2, 0.7]
    time = [0, 1, 2]

    print("\n==== Testing average() ====\n")

    for test in test_cases:
        print(f"\nTest: {test['name']}")
        data = test["data"]
        try:
            for mode in modes:
                print(f"\n  Mode: {mode}")
                try:
                    if mode == 'weighted':
                        result = average(data, mode=mode, weights=weights)
                    elif mode == 'moving':
                        result = average(data, mode=mode, window=2)
                    elif mode == 'trapezoidal':
                        result = average(data, mode=mode, time=time)
                    else:
                        result = average(data, mode=mode)
                    pprint(result)
                except Exception as e:
                    print(f"    [Error] {e}")
        except Exception as err:
            print(f"[Critical Error] {err}")
