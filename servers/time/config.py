import os

DEFAULT_TIME_FORMAT = os.getenv("DEFAULT_TIME_FORMAT", "%Y-%m-%d %H:%M:%S")
DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "UTC")

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
ALLOW_CREDENTIALS = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"

