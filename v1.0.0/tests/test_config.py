from pathlib import Path

import pytest
import yaml

from engine.config import load_game_config


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "game.yaml"


def test_default_game_config():
    config = load_game_config(DEFAULT_CONFIG)

    assert (config.map_width_m, config.map_height_m) == (128, 128)
    assert config.tick_s == 0.2


@pytest.mark.parametrize(
    ("section", "key", "value", "error"),
    [
        ("map", "width_m", 0, "map_width_m"),
        ("map", "width_m", -128, "map_width_m"),
        ("map", "width_m", True, "map_width_m"),
        ("map", "width_m", "128", "map_width_m"),
        ("map", "height_m", 0, "map_height_m"),
        ("simulation", "tick_s", 0, "tick_s"),
        ("simulation", "tick_s", -0.2, "tick_s"),
        ("simulation", "tick_s", float("nan"), "tick_s"),
        ("simulation", "tick_s", float("inf"), "tick_s"),
    ],
)
def test_reject_invalid_game_config(tmp_path, section, key, value, error):
    document = yaml.safe_load(DEFAULT_CONFIG.read_text(encoding="utf-8"))
    document[section][key] = value
    invalid_config = tmp_path / "invalid.yaml"
    invalid_config.write_text(yaml.safe_dump(document), encoding="utf-8")

    with pytest.raises(ValueError, match=error):
        load_game_config(invalid_config)
