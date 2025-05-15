from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Input schema for student registration
class StudentCreate(BaseModel):
    regno: str
    first_name: str
    middle_name: Optional[str] = None  # Optional middle name
    last_name: str
    email: EmailStr
    password: str  # Plain text password (will be hashed before storing)
    year_of_study: int
    phone_number: str
    role: str = "student"  # Role is fixed to "student"
    programme: str

    # Optional validation method to ensure role is 'student'
    def validate_role(self):
        if self.role != "student":
            raise ValueError("Role must be 'student'.")
        return self

    class Config:
        # This allows us to use the pydantic model for sqlalchemy models as well
        form_attributes = True

# Output schema for student response (for API response)
class StudentResponse(BaseModel):
    regno: str
    first_name: str
    middle_name: str
    last_name: str
    email: EmailStr
    programme: str
    year_of_study: int
    phone_number: str

    class Config:
        form_attributes = True  # To read data from SQLAlchemy models

# Input schema for instructor registration
class InstructorCreate(BaseModel):
    id: int
    first_name: str
    middle_name: Optional[str] = None  # Optional middle name
    last_name: str
    email: EmailStr
    password: str  # Plain text password (will be hashed before storing)
    phone_number: str
    role: str = "instructor"  # Role is fixed to "instructor"

    class Config:
        # This allows us to use the pydantic model for sqlalchemy models as well
        from_attributes = True

# Output schema for instructor response (for API response)
class InstructorResponse(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    role: str

    class Config:
        from_attributes = True  # To read data from SQLAlchemy models

# Generic user response schema for login purposes (optional)
class UserResponse(BaseModel):
    username: str
    role: str

    class Config:
        from_attributes = True  # To read data from SQLAlchemy models

class AttendanceResponse(BaseModel):
    id: int
    student_id: int
    session_id: int
    attendance_status: str
    recorded_at: datetime

    class Config:
        from_attributes = True  # Important for FastAPI to convert SQLAlchemy models to Pydantic models

class AttendanceCreate(BaseModel):
    student_id: str
    session: int
    timestamp: datetime