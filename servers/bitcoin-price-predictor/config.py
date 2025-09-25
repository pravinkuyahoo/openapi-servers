import os

BITCOIN_DATA_CSV = os.getenv("BITCOIN_DATA_CSV", "btcusd_1-min_data.csv")

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
ALLOW_CREDENTIALS = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"

