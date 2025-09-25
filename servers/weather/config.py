import os

OPEN_METEO_URL = os.getenv("OPEN_METEO_URL", "https://api.open-meteo.com/v1/forecast")

_fh_countries = os.getenv("FAHRENHEIT_COUNTRIES", "US,LR,MM")
FAHRENHEIT_COUNTRIES = {c.strip().upper() for c in _fh_countries.split(",") if c.strip()}

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
ALLOW_CREDENTIALS = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"

