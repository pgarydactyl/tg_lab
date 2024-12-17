from dataclasses import dataclass, asdict
import json
from pathlib import Path
import os

import tyro

from tg_lab.tis_camera.image_acquisition import process_on_trigger
from tg_lab.utils import get_event_id


@dataclass
class EventCountConfig:
    output_dir: str
    threshold: float = 100
    mode: int = 1
    nxnarea: int = 5
    multiply_factor: int = 10
    int_offset: int = 10
    event_size: int = 1
    debug_mode: bool = False

    def __post_init__(self):
        self.output_dir = str(Path(self.output_dir).absolute())


def entry_point(config: EventCountConfig):
    path = Path(config.output_dir) / get_event_id(name="event_count")
    os.makedirs(path)

    with open(path / "config.json", "w") as f:
        json.dump(asdict(config), f, indent=4)

    process_on_trigger(
        str(path),
        config.threshold,
        config.mode,
        config.nxnarea,
        config.multiply_factor,
        config.int_offset,
        config.event_size,
        config.debug_mode,
    )


if __name__ == "__main__":
    config = tyro.cli(EventCountConfig)
    entry_point(config)
