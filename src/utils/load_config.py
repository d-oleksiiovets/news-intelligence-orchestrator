from pathlib import Path
import yaml

def load_config(filepath: Path | str = None) -> dict:
    if filepath is None:
        filepath = Path(__file__).parent.parent.parent / "config.yaml"

    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(f"Config file not found: {filepath}")

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except yaml.YAMLError as e:
        raise RuntimeError(f"Failed to parse YAML config: {e}")