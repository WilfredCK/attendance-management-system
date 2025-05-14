# This is for my Database models (Student, User, Attendance, etc.)
from pydantic import BaseModel

# User model for registration and login
class User(BaseModel):
    username: str
    password: str # This will be a plain password (will be hashed in the backend)
    role: str  # admin, instructor, student

class UserLogin(BaseModel):
    username: str
    password: str
