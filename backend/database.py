# database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Replace values with your actual PostgreSQL credentials
DATABASE_URL = "postgresql://avnadmin:AVNS_bKzM-7DlMl2rZEt0qFj@http://pg-3e75bd31-face-matcher.c.aivencloud.com/defaultdb"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# SessionLocal class to be used for DB sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for your models
Base = declarative_base()
