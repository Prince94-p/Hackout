import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./carbon_core.db")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    if DATABASE_URL.startswith("sqlite"):
        SECRET_KEY = "carbon_core_secret_key_default_development_key"
    else:
        raise ValueError("SECRET_KEY environment variable is missing. It is required for production.")

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
