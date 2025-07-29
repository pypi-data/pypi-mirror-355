import json
from pathlib import Path


def read(file_path: str):
    """Read the configuration file."""
    config_path = Path(file_path).expanduser()
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file {file_path} is not found. "
            "Please try again after running 'touch {config_file}'."
        )
    with config_path.open() as f:
        return json.load(f)


def value(file_path: str, key: str):
    """Given the key, get the value from the config JSON."""
    value = read(file_path).get(key, None)
    if value is None:
        raise ValueError(f"No '{key}' is found in your config file.")
    return value
