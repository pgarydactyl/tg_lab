from collections import deque, defaultdict
from functools import partial
from typing import List

import numpy as np
import polars as pl
from skimage import feature


def get_ion_signals(
    data: np.array,
    integration_fns: List[str] = ["box"],
    **kwargs,
) -> pl.DataFrame:
    """
    Calculate ion positions, approximate size, and then integrated signals

    Args:
        data: Ion image data matrix
        integration_fns: List of integration function names to evaluate the
            ion signals with
        kwargs: Key work arguments for `skimage.feature.blob_doh`, the ion
            position and size identifier

    Returns:
        (pl.DataFrame): DataFrame containing the processed ion data
    """
    blobs = feature.blob_doh(
        data,
        min_sigma=1,
        max_sigma=30,
        num_sigma=12,
        threshold_rel=0.5,
        **kwargs,
    )

    res = defaultdict(list)
    for row, col, r in blobs:
        row, col = int(row), int(col)
        res["row"].append(row)
        res["col"].append(col)
        res["radius"].append(r)

        for integration_fn in integration_fns:
            fn = _integration_fns[integration_fn]
            res[f"{integration_fn}_sum"].append(fn(data, row, col, r))

    return pl.DataFrame(res)


def _integrate_box(data: np.array, row: int, col: int, r: float) -> float:
    """
    Integrate a boxed region around a provided center point. The area will be
    of dimensions (2r+1, 2r+1).

    Args:
        data: Ion image data matrix
        row: row index of the center point to integrate around
        col: column index of the center point to integrate around
        r: radius of region around the center point to integrate around
    """
    max_rows, max_cols = data.shape

    r = int(np.ceil(r))
    lrow = max(0, row - r)
    hrow = min(max_rows, row + r)
    lcol = max(0, col - r)
    hcol = min(max_cols, col + r)

    return data[lrow:hrow, lcol:hcol].sum()


def _integrate_norm(data: np.array, row: int, col: int, r: float, **kwargs) -> float:
    """
    Integrate a circular region with radius r around a provided center point
    whos outer edge is defined by a norm order

    Args:
        data: Ion image data matrix
        row: row index of the center point to integrate around
        col: column index of the center point to integrate around
        r: radius of region around the center point to integrate around
        kwargs: additional arguments to pass to `numpy.linalg.norm`
            e.g. `ord` defining the order of the norm

    Returns:
        (float): integrated value of region surrounding input center point
    """
    irow, icol = row, col
    max_rows = len(data)
    max_cols = len(data[0])
    r = np.ceil(r)

    res = 0
    seen = set()
    queue = deque([(row, col)])
    while queue:
        row, col = queue.popleft()
        seen.add((row, col))
        res += data[row, col]

        for dy, dx in ((1, 0), (0, 1), (-1, 0), (0, -1)):
            nrow, ncol = row + dy, col + dx
            if (nrow, ncol) in seen:
                continue
            if nrow < 0 or ncol < 0:
                continue
            if nrow >= max_rows or ncol >= max_cols:
                continue
            if (
                np.linalg.norm(
                    np.array((nrow, ncol)) - np.array((irow, icol)),
                    **kwargs,
                )
                > r
            ):
                continue

            queue.append((nrow, ncol))

    return res


_integration_fns = {
    "l1": partial(_integrate_norm, ord=1),
    "l2": partial(_integrate_norm, ord=2),
    "box": _integrate_box,
}
