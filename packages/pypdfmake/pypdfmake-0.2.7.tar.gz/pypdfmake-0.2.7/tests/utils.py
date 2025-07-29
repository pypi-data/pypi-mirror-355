from pathlib import Path
import json
from typing import Any


def load_expected_json(filename: str) -> dict[str, Any]:
    # Construct the full path to the expected_outputs directory
    current_dir = Path(__file__).resolve().parent
    expected_output_dir = current_dir / "expected_outputs"
    filepath = expected_output_dir / filename
    with filepath.open("r") as f:
        return json.load(f)
