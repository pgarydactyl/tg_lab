from .constants import RawIndices
import polars as pl


def find_peak(data, mz_range, threshold):
    col = pl.col(RawIndices.SIGNAL.value)
    data = filter_by_mz_range(data, mz_range)
    peaks = data.filter((col == col.min()) & (col.min() < threshold))
    rows = peaks.shape[0]
    return peaks[rows // 2]


def integrate_peak(signal, peak_index):
    i = peak_index
    j = peak_index

    while signal[i] < 0:
        i += 1

    while signal[j] < 0:
        j -= 1

    return sum(signal[j : i + 1]), (j, i)


def filter_by_mz_range(data: pl.DataFrame, mz_range: tuple[float]):
    x_min, x_max = mz_range
    col = pl.col(RawIndices.MZ.value)
    return data.filter((col > x_min) & (col < x_max))
