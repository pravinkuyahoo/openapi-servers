import os
from typing import Optional, List

from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN: Optional[str] = os.getenv("SLACK_BOT_TOKEN")
SLACK_TEAM_ID: Optional[str] = os.getenv("SLACK_TEAM_ID")
SLACK_CHANNEL_IDS_STR: Optional[str] = os.getenv("SLACK_CHANNEL_IDS")
SERVER_API_KEY: Optional[str] = os.getenv("SERVER_API_KEY")

PREDEFINED_CHANNEL_IDS: Optional[List[str]] = (
    [cid.strip() for cid in SLACK_CHANNEL_IDS_STR.split(",")] if SLACK_CHANNEL_IDS_STR else None
)

ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
ALLOW_CREDENTIALS = os.getenv("ALLOW_CREDENTIALS", "false").lower() == "true"

