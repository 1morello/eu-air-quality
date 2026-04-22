"""EU Air Quality API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import joblib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# --- Load data ---
df = pd.read_csv(ROOT / "data/processed/aqi_dataset_all.csv")
df["date"] = pd.to_datetime(df["date"], format="mixed")

meta = pd.read_csv(ROOT / "data/processed/station_metadata.csv")

reg_model = joblib.load(ROOT / "models/xgb_regressor.joblib")
cls_model = joblib.load(ROOT / "models/xgb_classifier.joblib")
label_enc = joblib.load(ROOT / "models/label_encoder.joblib")

with open(ROOT / "models/feature_config.json") as f:
    FEATURES = json.load(f)["features"]

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
    return {
        "status": "ok",
        "stations": df["station_id"].nunique(),
        "date_range": f"{df['date'].min().date()} to {df['date'].max().date()}",
    }


@app.get("/map")
def map_data(period: str = "recent"):
    """Stations with avg AQI. period: 'recent', '2024', '2023', etc."""
    filtered = df

    if period == "recent":
        cutoff = df["date"].max() - pd.Timedelta(days=30)
        filtered = df[df["date"] >= cutoff]
    elif period == "all":
        pass
    elif period.isdigit():
        filtered = df[df["date"].dt.year == int(period)]

    aqi_avg = (
        filtered.groupby("station_id")
        .agg(avg_aqi=("aqi", "mean"), country=("country", "first"))
        .reset_index()
    )

    merged = aqi_avg.merge(
        meta[["station_id", "station_name", "lat", "lon", "area_type", "station_type"]],
        on="station_id",
        how="inner",
    )

    merged["avg_aqi"] = merged["avg_aqi"].round(1)
    return merged.to_dict(orient="records")


@app.get("/station/{station_id}")
def station_data(station_id: str):
    sub = df[df["station_id"] == station_id]
    cols = ["date", "aqi", "aqi_category", "PM2.5", "PM10", "NO2", "O3"]
    result = sub[cols].sort_values("date").tail(365)
    result["date"] = result["date"].dt.strftime("%Y-%m-%d")
    result = result.fillna(0)
    return result.to_dict(orient="records")


@app.get("/predict/{station_id}")
def predict_station(station_id: str):
    """Predict tomorrow's AQI from station's latest data."""
    sub = df[df["station_id"] == station_id].sort_values("date")

    if len(sub) == 0:
        return {"error": "Station not found"}

    last = sub.iloc[-1]
    last7 = sub.tail(7)["aqi"].mean()

    features = {
        "CO_lag1": last.get("CO", 0) if pd.notna(last.get("CO")) else 0,
        "NO2_lag1": last.get("NO2", 0) if pd.notna(last.get("NO2")) else 0,
        "O3_lag1": last.get("O3", 0) if pd.notna(last.get("O3")) else 0,
        "PM10_lag1": last.get("PM10", 0) if pd.notna(last.get("PM10")) else 0,
        "PM2.5_lag1": last.get("PM2.5", 0) if pd.notna(last.get("PM2.5")) else 0,
        "SO2_lag1": last.get("SO2", 0) if pd.notna(last.get("SO2")) else 0,
        "aqi_lag1": last["aqi"] if pd.notna(last["aqi"]) else 50,
        "aqi_roll7": last7 if pd.notna(last7) else 50,
        "PM2.5_roll7": sub.tail(7)["PM2.5"].mean() if "PM2.5" in sub else 0,
        "PM10_roll7": sub.tail(7)["PM10"].mean() if "PM10" in sub else 0,
        "month": int(last["date"].month),
        "day_of_week": int(last["date"].dayofweek),
        "day_of_year": int(last["date"].dayofyear),
        "country_code": 0,
    }

    features = {k: (0 if pd.isna(v) else v) for k, v in features.items()}

    X = pd.DataFrame([features])[FEATURES]
    aqi_pred = float(reg_model.predict(X)[0])
    cat_pred = label_enc.inverse_transform(cls_model.predict(X))[0]

    return {
        "aqi": round(aqi_pred, 1),
        "category": cat_pred,
        "based_on": last["date"].strftime("%Y-%m-%d"),
        "current_aqi": round(float(last["aqi"]), 1) if pd.notna(last["aqi"]) else None,
        "current_category": last["aqi_category"] if pd.notna(last.get("aqi_category")) else None,
    }
