import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"


def main():
    # Check individual files
    csvs = sorted(PROCESSED.glob("*_*.csv"))
    csvs = [f for f in csvs if f.name != "daily_pollutants.csv"]

    print(f"Individual files: {len(csvs)} / 36 expected\n")
    for f in csvs:
        size = f.stat().st_size / (1024 * 1024)
        print(f"  {f.name:25s}  {size:.1f} MB")

    # Check merged file
    merged = PROCESSED / "daily_pollutants.csv"
    if merged.exists():
        df = pd.read_csv(merged)
        print(f"\n=== Merged dataset ===")
        print(f"Total rows: {len(df):,}")
        print(f"Countries: {sorted(df['country'].unique())}")
        print(f"Pollutants: {sorted(df['pollutant'].unique())}")
        print(f"\nRows per country:")
        print(df.groupby("country").size())
        print(f"\nRows per pollutant:")
        print(df.groupby("pollutant").size())
    else:
        print("\nMerged file not found — run merge manually if needed")


if __name__ == "__main__":
    main()
