import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"

csv_path = PROCESSED / "daily_pollutants.csv"

if csv_path.exists():
    df = pd.read_csv(csv_path)
    print(f"Total rows: {len(df):,}")
    print(f"\nCountries: {df['country'].unique()}")
    print(f"\nPollutants: {df['pollutant'].unique()}")
    print(f"\nRows per country:")
    print(df.groupby("country").size())
    print(f"\nRows per pollutant:")
    print(df.groupby("pollutant").size())
else:
    print("No CSV found yet")
