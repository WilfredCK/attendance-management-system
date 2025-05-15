# auth.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from models import Student, Instructor
from database import get_db  # Assuming you have a function to get the database session
from security import create_access_token, verify_password  # Assuming you have these helper functions
import os

# Create an instance of PassLib's CryptContext for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Create an APIRouter instance
router = APIRouter()

# User Login (for both student and instructor)
@router.post("/login/")
def login_user(email: str, password: str, db: Session = Depends(get_db)):
    user = None
    role = None

    # Try to find user in students table
    student = db.query(Student).filter(Student.email == email).first()
    if student and verify_password(password, student.password):
        user = student
        role = "student"

    # If not a student, try instructors
    if not user:
        instructor = db.query(Instructor).filter(Instructor.phone_number == email).first()
        if instructor and verify_password(password, instructor.password):
            user = instructor
            role = "instructor"

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Create token with role
    token_data = {"sub": user.email if role == "student" else user.phone_number, "role": role}
    access_token = create_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}

# Helper function to verify the password using PassLib
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Helper function to create an access token (use any JWT library like PyJWT)
def create_access_token(data: dict):
    import jwt  # You should install PyJWT if not already installed
    
    # Define secret key and expiration time for the token
    secret_key = os.getenv("JWT_SECRET_KEY", "default_secret_key")  # Use environment variable for security
    algorithm = "HS256"
    expires_delta = timedelta(hours=1)
    
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt
