"""
Helpers to load / persist baseline assumptions in YAML.
"""

from pathlib import Path
import yaml

_DEFAULTS_FILE = Path(__file__).with_name("defaults.yml")


def load_defaults() -> dict:
    """Return the baseline parameter dictionary."""
    with _DEFAULTS_FILE.open() as f:
        return yaml.safe_load(f)


def save_defaults(params: dict) -> None:
    """Overwrite defaults.yml (for power users / admins)."""
    with _DEFAULTS_FILE.open("w") as f:
        yaml.safe_dump(params, f, sort_keys=False)
