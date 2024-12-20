from enum import Enum


class ExperimentIndices(str, Enum):

    TITLE = "title"
    RUN = "run"
    REACTION_TIME = "reaction_time"


class RawIndices(str, Enum):

    RUN = ExperimentIndices.RUN.value
    TOF_TIME = "tof_time"
    SIGNAL = "signal"
    MZ = "m/z"


class PeakIndices(str, Enum):

    ROW_NR = "row_nr"
    SUM = "sum"
    TOF_TIME = RawIndices.TOF_TIME.value
    SIGNAL = RawIndices.SIGNAL.value
    MZ = RawIndices.MZ.value
    ION = "ion"
    MZ_SPAN = "m/z_span"
