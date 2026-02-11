import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# DeGiro credentials
DEGIRO_USERNAME = os.getenv("DEGIRO_USERNAME")
DEGIRO_PASSWORD = os.getenv("DEGIRO_PASSWORD")
DEGIRO_TOTP_SECRET = os.getenv("DEGIRO_TOTP_SECRET")

# Database
DB_PATH = os.getenv("DB_PATH", str(Path(__file__).parent / "portfolio.db"))

# Schedule (default: 18:00 daily — after EU market close)
SCHEDULE_HOUR = int(os.getenv("SCHEDULE_HOUR", "18"))
SCHEDULE_MINUTE = int(os.getenv("SCHEDULE_MINUTE", "0"))
