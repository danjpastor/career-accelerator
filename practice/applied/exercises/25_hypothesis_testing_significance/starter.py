"""Applied Lab 25: Perform and interpret a hypothesis test."""

from pathlib import Path
import json
import math
import statistics

try:
    import pandas as pd
except ImportError:
    pd = None


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "practice" / "applied" / "datasets" / "experimentation"





def main() -> None:
    print("Dataset folder:", DATA)
    if pd is None:
        print(
            "pandas is not installed. The lab can also be completed "
            "with csv, json, math, and statistics from the standard library."
        )

    # TODO: implement the exercise.
    # Keep calculations reproducible and include explicit validation.


if __name__ == "__main__":
    main()
