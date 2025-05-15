from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL for PostgreSQL (ensure it's securely stored and not hard-coded in production)
SQLALCHEMY_DATABASE_URL = "postgresql://avnadmin:AVNS_bKzM-7DlMl2rZEt0qFj@pg-3e75bd31-face-matcher.c.aivencloud.com:13086/facial-recognition" 

# Create an engine that knows how to connect to your PostgreSQL database
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)  # 'echo=True' logs SQL queries for debugging

# Create a sessionmaker bound to the engine, enabling interaction with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all the SQLAlchemy models (Student, Instructor, etc.)
Base = declarative_base()

# Dependency function to get the database session for use in the FastAPI routes
def get_db():
    db = SessionLocal()  # Create a new database session
    try:
        yield db  # Yield the session to be used in FastAPI route handlers
    finally:
        db.close()  # Close the session after it's used
