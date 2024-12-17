# main.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Cookie
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, update
from app.models.models import User, VerificationCode
import jwt
import secrets
from email.message import EmailMessage
import aiosmtplib
from app.db.database import get_async_db
from fastapi.responses import JSONResponse

from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES = 15
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Email settings
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM")

# Database setup
database = get_async_db()

# Models
class EmailVerification(BaseModel):
    email: EmailStr

class VerifyCode(BaseModel):
    email: EmailStr
    code: str

class Token(BaseModel):
    access_token: str
    token_type: str


router = APIRouter()

# Email sending utility
async def send_verification_email(email: str, code: str):
    message = EmailMessage()
    message["From"] = SMTP_FROM
    message["To"] = email
    message["Subject"] = "Your verification code"
    message.set_content(f"Your verification code is: {code}\nValid for {EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES} minutes.")

    smtp = aiosmtplib.SMTP(
        hostname=os.getenv("SMTP_HOST"),
        port=os.getenv("SMTP_PORT"),
        use_tls=False,
        timeout=10
    )

    try:
        await smtp.connect()
        await smtp.login(SMTP_USER, SMTP_PASSWORD)
        await smtp.send_message(message)
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send verification email")
    finally:
        await smtp.quit()

# Generate verification code
def generate_verification_code():
    return secrets.token_hex(3)  # 6 character code

# Create access token
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Routes
@router.post("/request-code")
async def request_verification_code(email_data: EmailVerification, background_tasks: BackgroundTasks):
    code = generate_verification_code()
    expires_at = datetime.utcnow() + timedelta(minutes=EMAIL_VERIFICATION_TOKEN_EXPIRE_MINUTES)
    
    async with get_async_db() as db:
        query = VerificationCode.__table__.insert().values(
            email=email_data.email,
            code=code,
            expires_at=expires_at
        )
        await db.execute(query)
        await db.commit()

        # Send email in background
        background_tasks.add_task(send_verification_email, email_data.email, code)
        
        return {"message": "Verification code sent"}

@router.post("/verify-code", response_model=Token)
async def verify_code(verify_data: VerifyCode):
    query = select(VerificationCode).where(
        VerificationCode.email == verify_data.email,
        VerificationCode.code == verify_data.code,
        VerificationCode.used == False,
        VerificationCode.expires_at > datetime.utcnow()
    ).order_by(VerificationCode.created_at.desc()).limit(1)
    
    async with get_async_db() as db:
        result = await db.execute(query)
        row = result.scalar_one_or_none()
    
        if not row:
            raise HTTPException(
                status_code=400,
                detail="Invalid or expired verification code"
            )
        
        # Mark code as used
        await db.execute(
            update(VerificationCode)
            .where(VerificationCode.id == row.id)
            .values(used=True)
        )
        await db.commit()
        
        # Create or get user
        user_query = select(User).where(User.email == verify_data.email)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user:
            new_user = User(email=verify_data.email, is_active=True)
            db.add(new_user)
            await db.commit()
        
    # Create access token
    access_token = create_access_token(
        data={"sub": verify_data.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    response = JSONResponse({"status": "authenticated"})
    
    # Set secure cookie
    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,        # Cannot be accessed by JavaScript
        secure=True,         # Only sent over HTTPS
        samesite="strict",   # CSRF protection
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    
    return response

# OAuth2 scheme for protected routes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# use this for dependency injection
async def get_current_user(
    session_token: str = Cookie(None)
) -> User:
    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )
    
    try:
        payload = jwt.decode(
            session_token, 
            SECRET_KEY, 
            algorithms=[ALGORITHM]
        )
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=401, 
                detail="Invalid token"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=401, 
            detail="Invalid token"
        )
    
    # Get user from database
    user_query = "SELECT * FROM users WHERE email = :email"
    user = await database.fetch_one(
        user_query, 
        values={"email": email}
    )
    
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    return user

# Protected route example
@router.get("/users/me")
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.post("/logout")
async def logout():
    response = JSONResponse({"status": "logged out"})
    response.delete_cookie(
        key="session_token",
        httponly=True,
        secure=True,
        samesite="strict"
    )
    return response