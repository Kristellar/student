import os
import uuid
import smtplib
from email.message import EmailMessage
from fastapi import HTTPException, UploadFile
from passlib.context import CryptContext
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import configparser

# Load the configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')

# Fetch secret key and email credentials from the config file
secret_key = config['DEFAULT']['SECRET_KEY']
email_from = config['DEFAULT']['EMAIL_FROM']
email_password = config['DEFAULT']['EMAIL_PASSWORD']

ALLOWED_EXTENSIONS = {".jpg", ".jpeg"}

ALLOWED_PDF_EXTENSIONS = {".pdf"}

# Initialize CryptContext for password hashing
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Save image function with allowed extensions and unique filename generation
def save_image(image: UploadFile) -> str:
    extension = os.path.splitext(image.filename)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension. Only .jpg and .jpeg are allowed.")

    unique_filename = f"{uuid.uuid4().hex}{extension}"
    image_dir = "images"

    # Ensure the images directory exists
    os.makedirs(image_dir, exist_ok=True)

    image_path = os.path.join(image_dir, unique_filename)
    try:
        with open(image_path, "wb") as image_file:
            image_file.write(image.file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

    return unique_filename



def save_pdf(pdf: UploadFile) -> str:
    extension = os.path.splitext(pdf.filename)[1].lower()
    if extension not in ALLOWED_PDF_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid file extension. Only .pdf is allowed.")

    unique_filename = f"{uuid.uuid4().hex}{extension}"
    pdf_dir = "uploads/papers"

    # Ensure the directory exists
    os.makedirs(pdf_dir, exist_ok=True)

    pdf_path = os.path.join(pdf_dir, unique_filename)
    try:
        with open(pdf_path, "wb") as pdf_file:
            pdf_file.write(pdf.file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save PDF: {str(e)}")

    return unique_filename


# Function to hash passwords
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Function to verify passwords
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Add custom CORS middleware to the FastAPI application
def add_custom_cors_middleware(app):
    allowed_origins = ["http://127.0.0.1:5500"]  # Update this with your allowed origin

    class CustomCORSMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if request.method == "OPTIONS":
                response = Response()
                response.headers.update({
                    "Access-Control-Allow-Origin": allowed_origins[0],
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
                    "Access-Control-Allow-Headers": "X-Custom-Header, Content-Type, Authorization",
                    "Access-Control-Max-Age": "86400",
                    "Access-Control-Allow-Credentials": "true",
                })
                return response

            response = await call_next(request)
            origin = request.headers.get("Origin")
            if origin in allowed_origins:
                response.headers.update({
                    "Access-Control-Allow-Origin": origin,
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
                    "Access-Control-Allow-Headers": "X-Custom-Header, Content-Type, Authorization",
                    "Access-Control-Allow-Credentials": "true",
                })
            return response

    app.add_middleware(CustomCORSMiddleware)

# Function to send a congratulation email
async def send_congratulation_email(to_email: str, user_name: str):
    msg = EmailMessage()
    msg.set_content(f"Dear {user_name},\n\nCongratulations on your successful signup!\n\nBest regards,\nYour Team")
    msg["Subject"] = "Congratulations on Your Signup!"
    msg["From"] = email_from  # Use the email_from loaded from config.ini
    msg["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_from, email_password)  # Securely load credentials
            server.send_message(msg)
        return {"message": "Email sent successfully"}
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        raise HTTPException(status_code=500, detail="SMTP authentication failed")
    except Exception as e:
        print(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Error sending email")

# Function to send OTP email
async def send_otp_email(to_email: str, otp: str):
    msg = EmailMessage()
    msg.set_content(f"Your OTP for verification is {otp}.")
    msg["Subject"] = "Your OTP Code"
    msg["From"] = email_from  # Use the email_from loaded from config.ini
    msg["To"] = to_email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_from, email_password)  # Securely load credentials
            server.send_message(msg)
        return {"message": "OTP sent successfully"}
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {e}")
        raise HTTPException(status_code=500, detail="SMTP authentication failed")
    except Exception as e:
        print(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Error sending email")
