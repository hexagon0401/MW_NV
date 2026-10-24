"""Read and validate game settings without starting services or simulation."""

from dataclasses import dataclass
from math import isfinite
from pathlib import Path

import yaml


@dataclass(frozen=True)
class GameConfig:
    map_width_m: int
    map_height_m: int
    tick_s: float

    def __post_init__(self) -> None:
        for name in ("map_width_m", "map_height_m"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if (
            type(self.tick_s) not in (int, float)
            or not isfinite(self.tick_s)
            or self.tick_s <= 0
        ):
            raise ValueError("tick_s must be a finite positive number")


def load_game_config(path: str | Path) -> GameConfig:
    """Load UTF-8 YAML; reject invalid shapes and invalid game dimensions."""
    with Path(path).open(encoding="utf-8") as source:
        document = yaml.safe_load(source)
    if not isinstance(document, dict):
        raise ValueError("game config must be a mapping")
    map_settings = document.get("map")
    simulation = document.get("simulation")
    if not isinstance(map_settings, dict) or not isinstance(simulation, dict):
        raise ValueError("map and simulation must be mappings")
    return GameConfig(
        map_width_m=map_settings.get("width_m"),
        map_height_m=map_settings.get("height_m"),
        tick_s=simulation.get("tick_s"),
    )
