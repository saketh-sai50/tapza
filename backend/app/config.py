import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "tapza-super-secret-production-key-2026")
    JWT_SECRET = os.environ.get("JWT_SECRET", "tapza-jwt-access-token-secret-key-32505")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", str(INSTANCE_DIR / "tapza.db"))
    
    # Critical business requirement: strictly 4 minutes
    BROADCAST_WINDOW_SECONDS = 240
    
    JWT_EXPIRATION_HOURS = 24
    MOCK_PAYMENT_ENABLED = True
