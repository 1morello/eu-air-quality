"""EU Air Quality API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- Load data ---
df = pd.read_csv(ROOT / "data/processed/aqi_dataset.csv")
df["date"] = pd.to_datetime(df["date"])

meta = pd.read_csv(ROOT / "data/processed/station_metadata.csv")

reg_model = joblib.load(ROOT / "models/xgb_regressor.joblib")
cls_model = joblib.load(ROOT / "models/xgb_classifier.joblib")
label_enc = joblib.load(ROOT / "models/label_encoder.joblib")

with open(ROOT / "models/feature_config.json") as f:
    FEATURES = json.load(f)["features"]

# Map country names to codes
COUNTRY_MAP = {
    "Germany": "DE", "Spain": "ES", "France": "FR",
    "Italy": "IT", "Poland": "PL", "Netherlands": "NL",
}
meta["country_code"] = meta["country"].map(COUNTRY_MAP)
meta["station_id"] = meta["country_code"] + "_" + meta["station_code"]

# --- App ---
app = FastAPI(title="EU Air Quality API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "stations": df["station_id"].nunique()}


@app.get("/countries")
def countries():
    result = (
        df.groupby("country")["station_id"]
        .nunique()
        .reset_index()
        .rename(columns={"station_id": "stations"})
    )
    return result.to_dict(orient="records")


@app.get("/map")
def map_data(country: str = None):
    """Stations with coordinates and average AQI for map display."""
    aqi_avg = (
        df.groupby("station_id")
        .agg(avg_aqi=("aqi", "mean"), country=("country", "first"))
        .reset_index()
    )

    merged = aqi_avg.merge(
        meta[["station_id", "station_name", "lat", "lon", "area_type", "station_type"]],
        on="station_id",
        how="inner",
    )

    if country:
        merged = merged[merged["country"] == country]

    merged["avg_aqi"] = merged["avg_aqi"].round(1)
    return merged.to_dict(orient="records")


@app.get("/station/{station_id}")
def station_data(station_id: str):
    sub = df[df["station_id"] == station_id]
    cols = ["date", "aqi", "aqi_category", "PM2.5", "PM10", "NO2", "O3"]
    result = sub[cols].sort_values("date").tail(365)
    result["date"] = result["date"].dt.strftime("%Y-%m-%d")
    return result.to_dict(orient="records")


@app.get("/predict")
def predict(
    pm25: float = 0, pm10: float = 0, no2: float = 0,
    o3: float = 0, so2: float = 0, co: float = 0,
    aqi_yesterday: float = 50, aqi_7day: float = 50,
    month: int = 1, day_of_week: int = 0,
    day_of_year: int = 1, country_code: int = 0,
):
    features = {
        "CO_lag1": co, "NO2_lag1": no2, "O3_lag1": o3,
        "PM10_lag1": pm10, "PM2.5_lag1": pm25, "SO2_lag1": so2,
        "aqi_lag1": aqi_yesterday, "aqi_roll7": aqi_7day,
        "PM2.5_roll7": pm25, "PM10_roll7": pm10,
        "month": month, "day_of_week": day_of_week,
        "day_of_year": day_of_year, "country_code": country_code,
    }

    X = pd.DataFrame([features])[FEATURES]
    aqi_pred = float(reg_model.predict(X)[0])
    cat_pred = label_enc.inverse_transform(cls_model.predict(X))[0]

    return {"aqi": round(aqi_pred, 1), "category": cat_pred}
