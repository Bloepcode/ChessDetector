from dataclasses import dataclass


@dataclass
class Config:
    positions: ((int))
    minimum_change: int
    sim_for_stills: int

    process_image_size: (int)
