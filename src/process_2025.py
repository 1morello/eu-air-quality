"""Process 2025 data through the same pipeline as historical."""

import pandas as pd
import numpy as np
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"


def extract_station_id(station):
    if station.startswith("DE/"):
        m = re.search(r"DE_(\w+?)_", station)
        return f"DE_{m.group(1)}" if m else station
    elif station.startswith("ES/"):
        m = re.search(r"SP_(\d+)_", station)
        return f"ES_{m.group(1)}" if m else station
    elif station.startswith("FR/"):
        m = re.search(r"SPO-(FR\d+)", station)
        return f"FR_{m.group(1)}" if m else station
    elif station.startswith("IT/"):
        m = re.search(r"SPO\.(IT\w+?)_", station)
        return f"IT_{m.group(1)}" if m else station
    elif station.startswith("NL/"):
        m = re.search(r"SPO-(NL\d+)", station)
        return f"NL_{m.group(1)}" if m else station
    elif station.startswith("PL/"):
        m = re.search(r"SPO_(PL\w+?)_", station)
        return f"PL_{m.group(1)}" if m else station
    return station


AQI_BREAKPOINTS = {
    "PM2.5": [
        (0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 500.4, 301, 500),
    ],
    "PM10": [
        (0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150),
        (255, 354, 151, 200), (355, 424, 201, 300), (425, 604, 301, 500),
    ],
    "NO2": [
        (0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150),
        (361, 649, 151, 200), (650, 1249, 201, 300), (1250, 2049, 301, 500),
    ],
    "O3": [
        (0, 54, 0, 50), (55, 70, 51, 100), (71, 85, 101, 150),
        (86, 105, 151, 200), (106, 200, 201, 300),
    ],
    "SO2": [
        (0, 35, 0, 50), (36, 75, 51, 100), (76, 185, 101, 150),
        (186, 304, 151, 200), (305, 604, 201, 300), (605, 1004, 301, 500),
    ],
    "CO": [
        (0.0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150),
        (12.5, 15.4, 151, 200), (15.5, 30.4, 201, 300), (30.5, 50.4, 301, 500),
    ],
}


def calc_sub_index(value, pollutant):
    if pd.isna(value) or value < 0:
        return np.nan
    for c_low, c_high, i_low, i_high in AQI_BREAKPOINTS.get(pollutant, []):
        if c_low <= value <= c_high:
            return (i_high - i_low) / (c_high - c_low) * (value - c_low) + i_low
    return 500


def aqi_category(aqi):
    if pd.isna(aqi): return "Unknown"
    if aqi <= 50: return "Good"
    if aqi <= 100: return "Moderate"
    if aqi <= 150: return "Unhealthy (Sensitive)"
    if aqi <= 200: return "Unhealthy"
    if aqi <= 300: return "Very Unhealthy"
    return "Hazardous"


def main():
    # Load all 2025 CSVs
    files_2025 = sorted(PROCESSED.glob("*_2025.csv"))
    print(f"Found {len(files_2025)} files")

    df = pd.concat([pd.read_csv(f) for f in files_2025], ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    print(f"Total rows: {len(df):,}")

    # Extract station IDs
    df["station_id"] = df["station"].apply(extract_station_id)

    # Pivot
    df_pivot = df.pivot_table(
        index=["country", "station_id", "date"],
        columns="pollutant",
        values="value",
        aggfunc="mean"
    ).reset_index()
    df_pivot.columns.name = None
    print(f"After pivot: {len(df_pivot):,}")

    # Keep rows with PM
    has_pm = df_pivot.get("PM2.5", pd.Series(dtype=float)).notna() | df_pivot.get("PM10", pd.Series(dtype=float)).notna()
    df_clean = df_pivot[has_pm].copy()
    print(f"With PM data: {len(df_clean):,}")

    # Calculate AQI
    for poll in ["PM2.5", "PM10", "NO2", "O3", "SO2", "CO"]:
        if poll in df_clean.columns:
            df_clean[f"aqi_{poll}"] = df_clean[poll].apply(lambda v: calc_sub_index(v, poll))

    aqi_cols = [c for c in df_clean.columns if c.startswith("aqi_")]
    df_clean["aqi"] = df_clean[aqi_cols].max(axis=1)
    df_clean["aqi_category"] = df_clean["aqi"].apply(aqi_category)

    # Time features
    df_clean["year"] = df_clean["date"].dt.year
    df_clean["month"] = df_clean["date"].dt.month
    df_clean["day_of_week"] = df_clean["date"].dt.dayofweek
    df_clean["day_of_year"] = df_clean["date"].dt.dayofyear
    df_clean["season"] = df_clean["month"].map({
        12: "winter", 1: "winter", 2: "winter",
        3: "spring", 4: "spring", 5: "spring",
        6: "summer", 7: "summer", 8: "summer",
        9: "autumn", 10: "autumn", 11: "autumn",
    })

    print(f"Final shape: {df_clean.shape}")
    print(f"Date range: {df_clean['date'].min()} to {df_clean['date'].max()}")

    # Save
    df_clean.to_csv(PROCESSED / "aqi_dataset_2025.csv", index=False)
    print(f"Saved aqi_dataset_2025.csv")

    # Merge with historical
    hist = pd.read_csv(PROCESSED / "aqi_dataset.csv")
    combined = pd.concat([hist, df_clean], ignore_index=True)
    combined.to_csv(PROCESSED / "aqi_dataset_all.csv", index=False)
    print(f"\nCombined: {len(combined):,} rows")
    print(f"Saved aqi_dataset_all.csv")


if __name__ == "__main__":
    main()
