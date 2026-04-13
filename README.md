# EU Air Quality

Air quality analysis and prediction across the European Union.
Uses EEA monitoring data to calculate AQI and forecast pollution levels.

LUISS x Accenture.

## Structure

    notebooks/       analysis and modeling
    src/             reusable modules
    data/            raw and processed datasets (not tracked)
    models/          trained models
    backend/         FastAPI API
    frontend/        React dashboard
    docs/            presentation materials

## Setup

    git clone https://github.com/1morello/eu-air-quality.git
    cd eu-air-quality
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

## License

MIT
