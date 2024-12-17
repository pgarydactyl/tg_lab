from dataclasses import dataclass, asdict
import json
from pathlib import Path
import os
import datetime

import tyro

from tg_lab.tis_camera.image_acquisition import process_on_trigger
from tg_lab.utils import get_event_id


@dataclass
class EventCountConfig:
    output_dir: str
    max_images: int = 100
    threshold: float = 100
    mode: int = 1
    nxnarea: int = 5
    multiply_factor: int = 10
    int_offset: int = 10
    event_size: int = 1
    keyboard_control: bool = False

    def __post_init__(self):
        date = datetime.datetime.now().strftime("%Y%m%d")
        self.output_dir = f"D:\\Experimental_Data\\{date}\\{Path(self.output_dir)}"


def entry_point(config: EventCountConfig):
    path = Path(config.output_dir) / get_event_id(name="event_count")
    os.makedirs(path)
    print(f"    >Output location: {path}")

    with open(path / "config.json", "w") as f:
        json.dump(asdict(config), f, indent=4)

    process_on_trigger(
        output_dir=str(path),
        max_images=config.max_images,
        threshold=config.threshold,
        mode=config.mode,
        nxnarea=config.nxnarea,
        multiply_factor=config.multiply_factor,
        int_offset=config.int_offset,
        event_size=config.event_size,
        keyboard_control=config.keyboard_control,
    )


if __name__ == "__main__":
    config = tyro.cli(EventCountConfig)
    entry_point(config)
