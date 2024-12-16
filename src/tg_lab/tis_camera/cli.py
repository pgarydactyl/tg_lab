from dataclasses import dataclass

import tyro

from tg_lab.tis_camera.image_acquisition import process_on_trigger


@dataclass
class EventCountConfig:
    output_path: str
    threshold: float
    mode: int
    nxnarea: int
    multiply_factor: int
    int_offset: int
    event_size: int = 1


def entry_point(config: EventCountConfig):
    process_on_trigger(
        config.output_path,
        config.threshold,
        config.mode,
        config.nxnarea,
        config.multiply_factor,
        config.int_offset,
        config.event_size
    )


if __name__ == "__main__":
    config = tyro.cli(EventCountConfig)
    entry_point(config)
