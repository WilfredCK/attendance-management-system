# This is for my Database models (Student, User, Attendance, etc.)
# models.py
import enum
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from database import Base

# User Table (General user model)
# class User(Base):
#     __tablename__ = "users"

#     id = Column(Integer, primary_key=True, index=True)
#     username = Column(String, unique=True, index=True)
#     password = Column(String)
#     role = Column(String)  # Can be "student", "instructor", or "admin"

#     # Establish relationship to student and instructor tables based on role
#     student = relationship("Student", back_populates="user", uselist=False)
#     instructor = relationship("Instructor", back_populates="user", uselist=False)

# Students Table
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    regno = Column(String, unique=True, index=True)
    first_name = Column(String)
    middle_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String) 
    year_of_study = Column(Integer)
    phone_number = Column(String)
    role = Column(String)
    programme = Column(String)

    # Create a relationship to the user table
    # user_id = Column(Integer, ForeignKey("users.id"))
    # user = relationship("User", back_populates="student")

    # Relationship to attendance and facial embeddings
    attendances = relationship("Attendance", back_populates="student")
    facial_embeddings = relationship("FacialEmbedding", back_populates="student")

# Instructors Table
class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    middle_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    phone_number = Column(String)
    password = Column(String) 
    role = Column(String)  # role is also available in User model, so not essential here

    # Create a relationship to the user table
    # user_id = Column(Integer, ForeignKey("users.id"))
    # user = relationship("User", back_populates="instructor")

    class_sessions = relationship("ClassSession", back_populates="instructor")
    courses = relationship("Course", back_populates="instructor")

# Attendance Table
class AttendanceStatus(str, enum.Enum):
    Present = "Present"
    ABSENT = "Absent"
    LATE = "Late"

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    session_id = Column(Integer, ForeignKey("class_sessions.id"))
    attendance_status = Column(Enum(AttendanceStatus, name="attendance_status_enum", validate_strings=True),
    nullable=False)
    recorded_at = Column(DateTime)

    student = relationship("Student", back_populates="attendances")
    session = relationship("ClassSession", back_populates="attendances")

# Class Sessions Table
class ClassSession(Base):
    __tablename__ = "class_sessions"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"))
    venue = Column(String)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    instructor_id = Column(Integer, ForeignKey("instructors.id"))

    course = relationship("Course", back_populates="class_sessions")
    instructor = relationship("Instructor", back_populates="class_sessions")
    attendances = relationship("Attendance", back_populates="session")
    session_days = relationship("SessionDay", back_populates="session")

# Courses Table
class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_name = Column(String)
    course_code = Column(String)
    instructor_id = Column(Integer, ForeignKey("instructors.id"))

    instructor = relationship("Instructor", back_populates="courses")
    class_sessions = relationship("ClassSession", back_populates="course")

# Facial Embeddings Table
class FacialEmbedding(Base):
    __tablename__ = "facial_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    embedding = Column(String)  # Can be stored as a JSON or string for embeddings
    created_at = Column(DateTime)

    student = relationship("Student", back_populates="facial_embeddings")

# Session Days Table
class SessionDay(Base):
    __tablename__ = "session_days"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("class_sessions.id"))
    day_of_week = Column(String)

    session = relationship("ClassSession", back_populates="session_days")

