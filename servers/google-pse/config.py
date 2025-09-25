import os

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_PSE_CX = os.getenv("GOOGLE_PSE_CX")

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
ALLOW_CREDENTIALS = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"

