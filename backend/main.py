from fastapi import FastAPI, HTTPException, Depends, APIRouter
from schemas import StudentCreate,AttendanceCreate, StudentResponse, InstructorCreate, AttendanceResponse  # Import your Pydantic response model
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from typing import List
from sqlalchemy import text
from passlib.context import CryptContext  # For password hashing
from auth import login_user, router as auth_router
from sqlalchemy.orm import Session
from database import get_db  # Import get_db from database.py
from models import Attendance,AttendanceStatus, Student, Instructor, ClassSession, Course, FacialEmbedding, SessionDay  # Import your SQLAlchemy models
from sqlalchemy.exc import SQLAlchemyError
from fastapi.logger import logger
import logging
import traceback

# -------------------------------
# App and Security Setup
# -------------------------------
app = FastAPI()

# Include your routes here
app.include_router(auth_router)

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# -------------------------------
# JWT Helper Functions
# -------------------------------
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None or role is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return {"sub": username, "role": role}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_current_user(token: str = Depends(oauth2_scheme)):
    return decode_jwt_token(token)

@app.get("/test-db-connection")
def test_db_connection(db: Session = Depends(get_db)):
    try:
        # Simple raw SQL query to test connection
        db.execute(text("SELECT 1"))
        return {"message": "✅ Connected to PostgreSQL database!"}
    except Exception as e:
        print("🔥 Database connection failed:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Database connection failed")
# -------------------------------
# Routes for Authentication
# -------------------------------
@app.post("/register/student", response_model=StudentResponse)
def register_student(student: StudentCreate, db: Session = Depends(get_db)):
    try:
        # Check if student already exists
        db_student = db.query(Student).filter(Student.regno == student.regno).first()
        if db_student:
            raise HTTPException(status_code=400, detail="Student already exists")
        
         # Hash password and create student
        hashed_password = pwd_context.hash(student.password)
        new_student = Student(
            regno=student.regno,
            first_name=student.first_name,
            middle_name=student.middle_name,
            last_name=student.last_name,
            email=student.email,
            password=hashed_password,
            year_of_study=student.year_of_study,
            phone_number=student.phone_number,
            role="student",  # Ensure role is "student"
            programme=student.programme
        )
        
        db.add(new_student)
        db.commit()
        db.refresh(new_student)

        return StudentResponse(regno=new_student.regno,
                           first_name=new_student.first_name,
                           middle_name=new_student.middle_name,
                           last_name=new_student.last_name,
                           email=new_student.email,
                           programme=new_student.programme, 
                           year_of_study=new_student.year_of_study,
                           phone_number=student.phone_number,
                           )

    except HTTPException as http_exc:
        # Re-raise so FastAPI can return 400 with your custom message
        raise http_exc

    except Exception as e:
     # This will show up in your terminal
        logger.error("Error during student registration: %s", str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

    
@app.post("/register/instructor", response_model=dict)
def register_instructor(instructor: InstructorCreate, db: Session = Depends(get_db)):
    
    # Check if instructor already exists
    db_instructor = db.query(Instructor).filter(Instructor.email == instructor.email).first()
    if db_instructor:
        raise HTTPException(status_code=400, detail="Instructor already exists")

    hashed_password = pwd_context.hash(instructor.password)
    new_instructor = Instructor(
        id=instructor.id,
        first_name=instructor.first_name,
        middle_name=instructor.middle_name,
        last_name=instructor.last_name,
        email=instructor.email,
        phone_number=instructor.phone_number,
        password=hashed_password,
        role="instructor"  # Ensure role is "instructor"
    )
    
    db.add(new_instructor)
    db.commit()
    db.refresh(new_instructor)
    
    return {"message": "Instructor registered successfully"}

# OAuth2 token route
@app.post("/token/")  # Token route for login
def oauth2_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Check if user exists
    db_user = db.query(Student).filter(Student.regno == form_data.username).first() or db.query(Instructor).filter(Instructor.id == form_data.username).first()
    
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not pwd_context.verify(form_data.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Get role from user db (either student or instructor)
    role = db_user.role

    # Create JWT token with the role included
    token_data = {"sub": form_data.username, "role": role}
    access_token = create_access_token(data=token_data)

    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me/")
def get_me(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["sub"], "role": current_user["role"]}

# -------------------------------
# Attendance Routes
# -------------------------------

# POST: Mark attendance
@app.post("/mark-attendance/")
def mark_attendance(
    data: AttendanceCreate, 
    current_user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Determine student ID based on user role
    if current_user["role"] == "student":
        # Assuming current_user["sub"] holds the student id (not regno)
        student_regno = current_user["sub"]
    elif current_user["role"] == "instructor":
        # For admin/instructor, student_id must be provided in data
        student_regno = data.student_id
    else:
        raise HTTPException(status_code=403, detail="Access forbidden")

    # Check if student exists by id (assuming id field)
    student = db.query(Student).filter(Student.regno == student_regno).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check if attendance already marked for this session and student
    attendance = db.query(Attendance).filter(
        Attendance.student_id == student.id,
        Attendance.session_id == data.session  # ensure field is session_id
    ).first()

    if attendance:
        raise HTTPException(status_code=409, detail="Attendance already marked for this session")

    # Add new attendance record
    new_attendance = Attendance(
        student_id=student.id,
        recorded_at=data.timestamp,  # use correct field name for timestamp
        session_id=data.session, 
        attendance_status=AttendanceStatus.Present.value     # use correct field name for session id
    )

    db.add(new_attendance)
    db.commit()
    db.refresh(new_attendance)

    return {"message": "Attendance marked", "record": AttendanceResponse.model_validate(new_attendance)}


@app.get("/attendance/", response_model=list[AttendanceResponse])
def get_all_attendance(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] != "instructor":
        raise HTTPException(status_code=403, detail="Access forbidden: instructors only")
    
    # Query attendance records from the database
    attendance_records = db.query(Attendance).all()
    
    # Return the records as a list of AttendanceResponse models
    return attendance_records

@app.get("/attendance/{student_id}", response_model=dict)
def get_student_attendance(student_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user["role"] not in ["instructor"]:
        raise HTTPException(status_code=403, detail="Access forbidden: Instructors only")

    # Query the attendance records for the student
    records = db.query(Attendance).filter(Attendance.student_id == student_id).all()
    
    if not records:
        raise HTTPException(status_code=404, detail="No records found for this student")
    
    # Convert the records to Pydantic models
    response = [AttendanceResponse.model_validate(r) for r in records]

    # Return the student ID and their attendance records
    return {"student_id": student_id, "records": response}

# -------------------------------
# Basic Test Route
# -------------------------------
@app.get("/")
def home():
    return {"message": "Backend API is running!"}
