import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite:///./meal_planner.db"  # Default to SQLite for development
)

# For PostgreSQL in production, use:
# DATABASE_URL = "postgresql://username:password@localhost/meal_planner"

# Create engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite specific configuration
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False},  # Needed for SQLite
        echo=False  # Set to True to see SQL queries in logs
    )
else:
    # PostgreSQL configuration
    engine = create_engine(DATABASE_URL, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    """Database dependency for FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database utilities
def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all tables in the database (use with caution!)"""
    Base.metadata.drop_all(bind=engine)

def get_db_session():
    """Get a database session for scripts/utilities"""
    return SessionLocal()