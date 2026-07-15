"""Applied Lab 10: Aggregate and export analysis results with pandas."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "practice" / "applied" / "datasets" / "operations"

def main() -> None:
    print("Dataset folder:", DATA)
    # TODO: implement the lab and add validation checks.

if __name__ == "__main__":
    main()
