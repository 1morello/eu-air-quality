
#Downloads air quality measurement data from the EEA.
#with the airbase library


import airbase
import shutil
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

COUNTRIES = ["IT", "DE", "FR", "ES", "PL", "NL"]
POLLUTANTS = ["PM2.5", "PM10", "NO2", "O3", "SO2", "CO"]


def download_and_aggregate(client, country, pollutant):
    """Download one country/pollutant combo, aggregate to daily, save CSV."""

    safe_name = pollutant.replace(".", "")
    output = PROCESSED_DIR / f"{country}_{safe_name}.csv"

    if output.exists():
        print(f"\n--- {country} / {pollutant} --- already done, skipping")
        return

    print(f"\n--- {country} / {pollutant} ---")

    dl_dir = RAW_DIR / "tmp"
    dl_dir.mkdir(parents=True, exist_ok=True)

    try:
        r = client.request("Verified", country, poll=[pollutant])
        r.download(dl_dir)
    except Exception as e:
        print(f"  Download failed: {e}")
        shutil.rmtree(dl_dir, ignore_errors=True)
        return

    files = list((dl_dir / country).rglob("*.parquet"))
    if not files:
        print(f"  No files found")
        shutil.rmtree(dl_dir, ignore_errors=True)
        return

    print(f"  Reading {len(files)} files...")
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)

    # Clean
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")
    df = df[df["Validity"] != -1]
    df = df[df["Value"] >= 0]
    df = df[df["Value"] < 1000]

    df["date"] = df["Start"].dt.date
    df["station"] = df["Samplingpoint"]
    df["country"] = country
    df["pollutant"] = pollutant

    # Aggregate to daily averages
    daily = (
        df.groupby(["country", "station", "date", "pollutant"])["Value"]
        .mean()
        .reset_index()
        .rename(columns={"Value": "value"})
    )

    daily.to_csv(output, index=False)
    print(f"  Raw: {len(df):,} -> Daily: {len(daily):,}")
    print(f"  Saved to {output.name}")

    # Clean up raw files
    shutil.rmtree(dl_dir, ignore_errors=True)


def merge_all():
    """Merge all individual CSVs into one final dataset."""

    csvs = sorted(PROCESSED_DIR.glob("*_*.csv"))
    csvs = [f for f in csvs if f.name != "daily_pollutants.csv"]

    if not csvs:
        print("No data files found")
        return

    print(f"\nMerging {len(csvs)} files...")
    df = pd.concat([pd.read_csv(f) for f in csvs], ignore_index=True)
    df.to_csv(PROCESSED_DIR / "daily_pollutants.csv", index=False)
    print(f"Total: {len(df):,} rows")
    print(f"Countries: {sorted(df['country'].unique())}")
    print(f"Pollutants: {sorted(df['pollutant'].unique())}")


def main():
    client = airbase.AirbaseClient()
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    for country in COUNTRIES:
        for pollutant in POLLUTANTS:
            download_and_aggregate(client, country, pollutant)

    merge_all()
    print("\n=== Done ===")


if __name__ == "__main__":
    main()
