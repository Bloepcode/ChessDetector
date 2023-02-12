from dataclasses import dataclass


@dataclass
class Config:
    positions: ((int))
    minimum_change: int

    process_image_size: (int)
