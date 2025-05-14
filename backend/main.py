#This is my main FastAPI app and routes
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from typing import List
from passlib.context import CryptContext  # For password hashing
# Import your authentication functions
from auth import register_user, login_user, get_current_user
from models import User, UserLogin

# -------------------------------
# App and Security Setup
# -------------------------------
app = FastAPI()

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# -------------------------------
# In-memory "databases"
# -------------------------------
users_db = {}
students_db = {}         # key: student_id, value: Student
attendance_records = []  # list of Attendance


# -------------------------------
# Pydantic models for validation
# -------------------------------

class User(BaseModel):
    username: str
    password: str
    role: str

class Student(BaseModel):
    student_id: str
    name: str

class Attendance(BaseModel):
    student_id: str
    timestamp: datetime
    session: str

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

# -------------------------------
# Routes for Authentication
# -------------------------------
@app.post("/register/")
def register_user(user: User):
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = pwd_context.hash(user.password)
    users_db[user.username] = {
        "username": user.username,
        "hashed_password": hashed_password,
        "role": user.role
    }
    
     # 👇 Auto-register student if role is student
    if user.role == "student":
        if user.username in students_db:
            raise HTTPException(status_code=400, detail="Student already registered")
        students_db[user.username] = {
            "student_id": user.username,
            "name": user.username  # or ask for name explicitly
        }

    print(f"User registered: {user.username}")  # Debug log
    return {"message": "User registered successfully"}

from models import UserLogin  # use this instead of User

# OAuth2 token route
@app.post("/token/")
def oauth2_login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username not in users_db:
        raise HTTPException(status_code=404, detail="User not found")

    stored_hashed_password = users_db[form_data.username]["hashed_password"]
    if not pwd_context.verify(form_data.password, stored_hashed_password):
        raise HTTPException(status_code=401, detail="Invalid password")

    # Get role from user db
    role = users_db[form_data.username]["role"]

    # Create JWT token
    token_data = {
        "sub": form_data.username,
        "role": role
    }
    access_token = create_access_token(data=token_data)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@app.get("/me/")
def get_me(current_user: dict = Depends(get_current_user)):
    return {"username": current_user["sub"], "role": current_user["role"]}

# -------------------------------
# Basic Test Route
# -------------------------------
@app.get("/")
def home():
    return {"message": "Backend API is running!"}
# -------------------------------
# Attendance Routes
# -------------------------------

# POST: Mark attendance

@app.post("/mark-attendance/")
def mark_attendance(data: Attendance, current_user: dict = Depends(get_current_user)):
    if current_user["role"] == "student":
        student_id = current_user["sub"]
    elif current_user["role"] in ["admin", "instructor"]:
        student_id = data.student_id
    else:
        raise HTTPException(status_code=403, detail="Access forbidden")

    if student_id not in students_db:
        raise HTTPException(status_code=404, detail="Student not found")

    for record in attendance_records:
        if record.student_id == student_id and record.session == data.session:
            raise HTTPException(status_code=409, detail="Already marked for this session")

    new_record = Attendance(
        student_id=student_id,
        timestamp=data.timestamp,
        session=data.session
    )
    attendance_records.append(new_record)
    return {"message": "Attendance marked", "record": new_record}


# GET: Get all attendance records
@app.get("/attendance/")
def get_all_attendance(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access forbidden: Admins only")
    return attendance_records


# GET: Get attendance for a student

@app.get("/attendance/{student_id}")
def get_student_attendance(student_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in ["admin", "instructor"]:
        raise HTTPException(status_code=403, detail="Access forbidden: Instructors or Admins only")

    records = [record for record in attendance_records if record.student_id == student_id]
    if not records:
        raise HTTPException(status_code=404, detail="No records found for this student")

    return {"student_id": student_id, "records": records}
