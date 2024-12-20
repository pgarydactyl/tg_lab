import matplotlib.pyplot as plt
import polars as pl
from pydantic import BaseModel, Field

from . import file_utils
from .constants import RawIndices, PeakIndices, ExperimentIndices
from . import data_utils as du


class BackgroundParams(BaseModel):
    """
    Parameters specifying what section of the data to calculate background statistics from
    The units of the parameters are `m/z`
    """

    x_min: float = 0
    x_max: float = 1

    def as_tuple(self):
        return (self.x_min, self.x_max)


class MZParams(BaseModel):
    a: float = 1.24
    b: float = 1.04
    c: float = 0.35

    def convert(self, t):
        return self.a * (t - self.b) ** 2 + self.c


class PeakParams(BaseModel):
    sigma: float = Field(default=6)
    peaks: dict[str, float] = Field(default_factory=lambda: {"Be": 9})
    peak_width: float = Field(default=1)

    def get_peak_detection_threshold(self, mean, std):
        return mean - (self.sigma * std)

    def get_peak_ranges(self):
        radius = self.peak_width / 2
        return {key: (val - radius, val + radius) for key, val in self.peaks.items()}


class Config(BaseModel):

    exclusions: dict[float, list[int]] = Field(default_factory=lambda: {0: []})
    bkg_params: BackgroundParams = Field(default_factory=BackgroundParams)
    mz_params: MZParams = Field(default_factory=MZParams)
    peak_params: PeakParams = Field(default_factory=PeakParams)


class TofData:

    def __init__(
        self,
        title: str,
        time: int | float,
        run: int,
        raw_data: pl.DataFrame,
        peak_data: pl.DataFrame | None = None,
        config: Config | None = None,
    ):
        pass
        self.title = title
        self.time = time
        self.run = run
        self.raw_data = raw_data
        self.peak_data = pl.DataFrame() if peak_data is None else peak_data
        self.config = Config() if config is None else config

    @classmethod
    def from_file(cls, path: str):
        title, time, run = file_utils.parse_file_path(path)
        data = file_utils.parse_data(path)
        return cls(
            title=title,
            time=float(time),
            run=int(run),
            raw_data=pl.DataFrame(data),
        )

    def copy(self, **kwargs):
        d = {**self.__dict__, **kwargs}
        return type(self)(**d)

    def get_experiment_cols(self):
        return [
            pl.lit(self.time).alias(ExperimentIndices.REACTION_TIME.value),
            pl.lit(self.run).alias(ExperimentIndices.RUN.value),
            pl.lit(self.title).alias(ExperimentIndices.TITLE.value),
        ]

    def convert_to_mz(self):
        data = self.raw_data.with_columns(
            self.config.mz_params.convert(
                self.raw_data[RawIndices.TOF_TIME.value]
            ).alias(RawIndices.MZ.value)
        )
        return self.copy(raw_data=data)

    def get_bkg_stats(self):
        signal = du.filter_by_mz_range(
            self.raw_data, self.config.bkg_params.as_tuple()
        ).select(RawIndices.SIGNAL.value)
        mean = signal.mean().item()
        std = signal.std().item()
        return mean, std

    def normalize_background(self):
        mean, _ = self.get_bkg_stats()
        data = self.raw_data.with_columns(pl.col(RawIndices.SIGNAL.value) - mean)

        return self.copy(raw_data=data)

    def find_peaks(self):
        mean, std = self.get_bkg_stats()
        threshold = self.config.peak_params.get_peak_detection_threshold(
            mean=mean, std=std
        )

        peak_data = []
        for name, mz_range in self.config.peak_params.get_peak_ranges().items():
            peak = du.find_peak(self.raw_data.with_row_count(), mz_range, threshold)
            peak_data.append(peak.with_columns(pl.lit(name).alias("ion")))

        if not peak_data:
            return self

        return self.copy(peak_data=pl.concat(peak_data))

    def integrate_peaks(self):
        signal = self.raw_data.get_column(RawIndices.SIGNAL.value).to_numpy()

        peak_data = []
        for row in self.peak_data.to_dicts():
            peak_sum, row_span = du.integrate_peak(
                signal, row[PeakIndices.ROW_NR.value]
            )
            mz_span = (
                self.raw_data.get_column(RawIndices.MZ.value).gather(row_span).to_list()
            )
            row[PeakIndices.SUM.value] = peak_sum
            row[PeakIndices.MZ_SPAN.value] = mz_span
            peak_data.append(row)

        return self.copy(peak_data=pl.DataFrame(peak_data))

    def process(self):
        return (
            self.convert_to_mz().normalize_background().find_peaks().integrate_peaks()
        )


class TofExperimentData:

    def __init__(self, path: str, data: list[TofData], config: Config | None = None):
        self.path = path
        self.data = data
        self.config = Config() if config is None else config

    @classmethod
    def from_directory(cls, path: str):
        return cls(
            path=path, data=[TofData.from_file(f) for f in file_utils.get_files(path)]
        )

    def copy(self, **kwargs):
        d = {**self.__dict__, **kwargs}
        return type(self)(**d)

    def get_keys(self):
        keys = {}
        for td in self.data:
            keys[td.time] = keys.get(td.time, [])
            keys[td.time].append(td.run)
        
        for k in keys:
            keys[k].sort()

        return keys

    def filter_by_exclusions(self):
        data = []
        for td in self.data:
            if (
                td.time in self.config.exclusions
                and td.run in self.config.exclusions[td.time]
            ):
                continue
            data.append(td)
        return self.copy(data=data)

    def process(self):
        ted = self.filter_by_exclusions()
        data = []
        for td in ted.data:
            td.config = self.config
            data.append(td.process())
        return self.copy(data=data)

    def get_combined_raw_data(self):
        combined = []
        for td in self.data:
            combined.append(td.raw_data.with_columns(td.get_experiment_cols()))

        return pl.concat(combined)

    def get_combined_peak_data(self):
        combined = []
        for td in self.data:
            combined.append(td.peak_data.with_columns(td.get_experiment_cols()))

        return pl.concat(combined)

    def get_normalization(self):
        peak_data: pl.DataFrame = self.get_combined_peak_data()
        return peak_data.group_by(
            [ExperimentIndices.REACTION_TIME.value, RawIndices.RUN.value]
        ).agg(pl.col(PeakIndices.SUM.value).sum().alias(ExperimentIndices.NORM.value))

    def get_normalized_combined_peak_data(self):
        norm = self.get_normalization()
        return self.get_combined_peak_data().join(
            norm, [ExperimentIndices.REACTION_TIME.value, RawIndices.RUN.value]
        ).with_columns(
            (
                pl.col(PeakIndices.SUM.value)
                / pl.col(ExperimentIndices.NORM.value)
            ).alias(ExperimentIndices.NORM_SUM.value)
        )

    def get_aggregated_peak_data(self):
        group_by_cols = [PeakIndices.ION.value, ExperimentIndices.REACTION_TIME.value]
        agg_col = pl.col(PeakIndices.SUM.value)
        return (
            self.get_combined_peak_data()
            .group_by(group_by_cols)
            .agg(
                agg_col.mean().alias("mean"),
                agg_col.std().alias("std"),
                agg_col.sum().alias("sum"),
                agg_col.count().alias("count")
            )
            .sort(group_by_cols)
        )
    
    def get_normalized_aggregated_peak_data(self):
        group_by_cols = [PeakIndices.ION.value, ExperimentIndices.REACTION_TIME.value]
        agg_col = pl.col(ExperimentIndices.NORM_SUM.value)
        return (
            self.get_normalized_combined_peak_data()
            .group_by(group_by_cols)
            .agg(
                agg_col.mean().alias("mean"),
                agg_col.std().alias("std"),
                agg_col.sum().alias("sum"),
                agg_col.count().alias("count")
            )
            .sort(group_by_cols)
        )

    def plot_raw(self, xlim=None, ylim=None, t: float | int | None = None):
        plotter = TofPlotter()
        ted = self.filter_by_exclusions()

        data = ted.data
        if t is not None:
            data = [td for td in ted.data if td.time == t]
        for td in data:
            td.config = self.config
            fig, ax = plotter.plot_raw(
                td=td.process(),
                xlim=xlim,
                ylim=ylim,
            )

    def save_data(self, path: str | None = None):
        if path is None:
            path = self.path
        output_dir = file_utils.prepare_experiment_dir(path)
        ted = self.process()
        file_utils.write_json(output_dir / "config.json", self.get_config())
        # drop MZ_SPAN because it's a tuple and csv's cannot handle that structure
        ted.get_normalized_combined_peak_data().drop(PeakIndices.MZ_SPAN.value).write_csv(
            output_dir / "combined_peak_data.csv"
        )
        ted.get_aggregated_peak_data().write_csv(
            output_dir / "aggregated_peak_data.csv"
        )
        ted.get_normalized_aggregated_peak_data().write_csv(
            output_dir / "normalized_aggregated_peak_data.csv"
        )

    def print_config(self):
        return self.config.model_dump_json(indent=4)

    def get_config(self):
        return self.config.model_dump()

    def set_config(self, params):
        self.config = Config(**params)


class TofPlotter:

    def _plot_background_range(self, ax, td):
        ax.fill_between(
            td.config.bkg_params.as_tuple(),
            0,
            1,
            color="b",
            alpha=0.2,
            transform=ax.get_xaxis_transform(),
            label="background_range",
        )

    def _plot_peak_threshold(self, ax, td):
        mean, std = td.get_bkg_stats()
        threshold = td.config.peak_params.get_peak_detection_threshold(
            mean=mean, std=std
        )
        ax.axhline(
            threshold,
            color="g",
            linestyle="dotted",
            alpha=0.5,
            label="peak_detection_threshold",
        )

    def _plot_peak_detection_ranges(self, ax, td):
        bottom, top = ax.get_ylim()
        left, right = ax.get_xlim()
        i = 0
        for name, peak_range in td.config.peak_params.get_peak_ranges().items():
            label = None
            if i == 0:
                label = "peak_detection_range"
            i += 1
            ax.fill_between(
                peak_range,
                0,
                1,
                color="white",
                alpha=0.3,
                edgecolor="g",
                hatch="///",
                transform=ax.get_xaxis_transform(),
                label=label,
            )
            if left > peak_range[0] or right < peak_range[1]:
                continue
            ax.text(
                x=peak_range[0],
                y=bottom,
                s=f" {name}",
                rotation="vertical",
                horizontalalignment="right",
                verticalalignment="bottom",
            )

    def _plot_peaks(self, ax, td):
        for row in td.peak_data.to_dicts():
            ax.fill_between(
                row["m/z_span"],
                0,
                1,
                color="r",
                alpha=0.3,
                transform=ax.get_xaxis_transform(),
            )

    def plot_raw(
        self,
        td: TofData,
        xlim: tuple[float] | None = None,
        ylim: tuple[float] | None = None,
    ):
        x = RawIndices.MZ.value
        y = RawIndices.SIGNAL.value

        fig, ax = plt.subplots()

        ax.plot(td.raw_data[x], td.raw_data[y], color="k", linewidth=0.5)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set(xlabel=x, ylabel=y)
        ax.set_title(f"{td.title}\ntime:{td.time} run:{td.run}")

        self._plot_background_range(ax=ax, td=td)
        self._plot_peak_threshold(ax=ax, td=td)
        self._plot_peak_detection_ranges(ax=ax, td=td)
        self._plot_peaks(ax=ax, td=td)

        ax.legend(bbox_to_anchor=(1, 1), loc="upper left")

        return fig, ax
