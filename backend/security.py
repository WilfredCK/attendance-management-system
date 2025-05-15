# security.py
# Handles password hashing and JWT token generation
import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import os
from typing import Optional

# Secret and JWT configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "default_secret_key")  # Load from environment variable or default
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # Token expires in 30 minutes

# Hash a plain-text password
def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.
    """
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

# Verify a password against its hashed version
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify if the plain-text password matches the hashed version.
    """
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

# Create a JWT access token
def create_access_token(data: dict, expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)) -> str:
    """
    Create a JWT token with user data (username and role).
    The token will expire after the defined time.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    
    # Encode the JWT with the secret key
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Decode and validate a JWT access token
def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate the JWT token, returning the payload if valid.
    """
    try:
        # Decode the token and verify its validity
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# Example helper function to extract the user info from the decoded token
def get_user_from_token(token: str) -> Optional[dict]:
    """
    Given a token, decodes it and returns the user info (username and role).
    """
    payload = decode_access_token(token)
    if payload:
        return {"username": payload.get("sub"), "role": payload.get("role")}
    return None
