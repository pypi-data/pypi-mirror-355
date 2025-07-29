from sqlalchemy import Column, Integer, String, Text, Date, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import text
import os

DB_PATH = os.environ.get("DB_PATH", "crm_umkm.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)

# Enable WAL mode for SQLite
with engine.connect() as conn:
    conn.execute(text("PRAGMA journal_mode=WAL;"))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()