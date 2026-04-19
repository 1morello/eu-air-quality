"""Parse station metadata from EEA."""

import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"


def main():
    # All metadata files are identical (contain all countries)
    # Just read one
    sample = RAW_DIR / "metadata" / "IT_metadata.tsv"

    meta = pd.read_csv(sample, on_bad_lines="skip")
    print(f"Shape: {meta.shape}")
    print(f"Columns: {list(meta.columns)}")

    # Filter our countries
    countries = ["Italy", "Germany", "France", "Spain", "Poland", "Netherlands"]
    meta = meta[meta["Country"].isin(countries)]

    # Keep useful columns
    cols = [
        "Country", "Air Quality Station EoI Code", "Air Quality Station Name",
        "Longitude", "Latitude", "Altitude", "Air Quality Station Area",
        "Air Quality Station Type",
    ]
    meta = meta[cols].drop_duplicates(subset=["Air Quality Station EoI Code"])

    # Rename for simplicity
    meta.columns = ["country", "station_code", "station_name",
                     "lon", "lat", "altitude", "area_type", "station_type"]

    print(f"\nFiltered: {len(meta)} stations")
    print(meta.head(10))

    meta.to_csv(PROCESSED_DIR / "station_metadata.csv", index=False)
    print(f"\nSaved to station_metadata.csv")


if __name__ == "__main__":
    main()
