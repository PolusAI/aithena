import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", None)

if DATABASE_URL is None:
    POSTGRES_USER = os.environ.get("POSTGRES_USER", None)
    POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", None)
    POSTGRES_HOST = os.environ.get("POSTGRES_HOST", None)
    POSTGRES_PORT = os.environ.get("POSTGRES_PORT", None)
    POSTGRES_DB = os.environ.get("POSTGRES_DB", None)
    DATABASE_URL = f"postgresql+psycopg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

if DATABASE_URL is not None:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")