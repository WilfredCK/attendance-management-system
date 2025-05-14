# This is for Handling user authentication (login, registration)
from jose import JWTError, jwt  
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

from models import User
from security import hash_password, verify_password, create_access_token, decode_access_token

# Secret key used for encoding and decoding the JWT token
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme instance
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# In-memory database to store users
fake_users_db = {}

# Register a new user
def register_user(user: User):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = hash_password(user.password)
    fake_users_db[user.username] = {"username": user.username, "password": hashed_password}
    
    return {"message": "User registered successfully"}

# Login a user and return a JWT token
def login_user(user: User):
    stored_user = fake_users_db.get(user.username)
    
    if not stored_user or not verify_password(user.password, stored_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token_data = {"sub": user.username}
    access_token = create_access_token(data=token_data)
    return {"access_token": access_token, "token_type": "bearer"}

# Dependency to get the current user from the JWT token
def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Decode the token to get the payload (which includes the role and user info)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # Extract the username (sub) and role from the payload
        username: str = payload.get("sub")
        role: str = payload.get("role")  # Assuming the role is part of the payload

        if username is None or role is None:
            raise HTTPException(status_code=401, detail="Token is invalid or expired")

        current_user = {"sub": username, "role": role}

        # Handle role-based access (you can modify this logic based on your needs)
        if role == "admin":
            # Admin has full access
            pass
        elif role == "instructor":
            # Instructor has limited access
            pass
        elif role == "student":
            # Student has the least access
            pass
        else:
            raise HTTPException(status_code=403, detail="Role not recognized")

        return current_user

    except JWTError:
        raise HTTPException(status_code=401, detail="Token is invalid or expired")
