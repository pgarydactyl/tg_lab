from collections import deque

import numpy as np
import polars as pl
from skimage import feature


def get_ion_signals(data: np.array, **kwargs) -> pl.DataFrame:
    blobs = feature.blob_doh(
        data,
        min_sigma=2,
        max_sigma=30,
        num_sigma=12,
        threshold_rel=0.5,
        **kwargs,
    )
    res = {"row": [], "col": [], "radius": [], "sum": []}
    for row, col, r in blobs:
        row, col = int(row), int(col)
        _sum = integrate(data, row, col, r)
        res["row"].append(row)
        res["col"].append(col)
        res["radius"].append(r)
        res["sum"].append(_sum)

    return pl.DataFrame(res)


def integrate(data: np.array, row: int, col: int, r: float) -> float:
    irow, icol = row, col
    max_rows = len(data)
    max_cols = len(data[0])

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
            if np.linalg.norm(np.array((nrow, ncol)) - np.array((irow, icol))) > r:
                continue

            queue.append((nrow, ncol))

    return res
