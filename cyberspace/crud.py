import configparser
import datetime
import random
import string
from typing import Optional
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from service import hash_password, save_image, save_pdf
from models import (
    User as UserModel,
    VirtualInternship as VirtualInternshipModel,
    Seminar as SeminarModel,
    Webinar as WebinarModel,
    ResearchPaper as ResearchPaperModel,
    OTP as OTPModel
)
from schemas import (
    UserCreate,
    VirtualInternship as VirtualInternshipSchema,
    Seminar as SeminarSchema,
    Webinar as WebinarSchema,
    ResearchPaper as ResearchPaperSchema
)
import jwt
from jwt.exceptions import PyJWTError as JWTError
from passlib.context import CryptContext




# Load the configuration from config.ini
config = configparser.ConfigParser()
config.read('config.ini')


algorithm = config['DEFAULT']['ALGORITHM']
secret_key = config['DEFAULT']['SECRET_KEY']



pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def create_user(db: Session, user: UserCreate, image: Optional[UploadFile] = None):
    # Check if a user with the same email or mobile number already exists
    existing_user = db.query(UserModel).filter(
        (UserModel.email_id == user.email_id) | 
        (UserModel.mobile_number == user.mobile_number)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400, 
            detail="A user with this email or mobile number already exists."
        )

    image_filename = None
    if image:
        image_filename = save_image(image)

    db_user = UserModel(
        first_name=user.first_name,
        last_name=user.last_name,
        email_id=user.email_id,
        mobile_number=user.mobile_number,
        college_name=user.college_name,
        hashed_password=hash_password(user.password),
        image_filename=image_filename
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="A user with this email or mobile number already exists."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return db_user

def get_user(db: Session, user_id: int):
    return db.query(UserModel).filter(UserModel.id == user_id).first()

def authenticate_user(db: Session, email_id: str, password: str):
    user = db.query(UserModel).filter(UserModel.email_id == email_id).first()
    if user and pwd_context.verify(password, user.hashed_password):
        return user
    return None


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire, "sub": data.get("sub")})  # Ensure 'sub' is included
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt

 
def get_user_profile(db: Session, token: str):
    try:
        # Decode the token to get user data
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Fetch user from the database
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user profile: {str(e)}")

def get_user_by_email(db: Session, email_id: str):
    return db.query(UserModel).filter(UserModel.email_id == email_id).first()

def create_virtual_internship(db: Session, internship: VirtualInternshipSchema, user_id: int):
    db_internship = VirtualInternshipModel(**internship.model_dump(), user_id=user_id)
    db.add(db_internship)
    db.commit()
    db.refresh(db_internship)
    return db_internship

def create_seminar(db: Session, seminar: SeminarSchema, user_id: int):
    db_seminar = SeminarModel(**seminar.model_dump(), user_id=user_id)
    db.add(db_seminar)
    db.commit()
    db.refresh(db_seminar)
    return db_seminar

def create_webinar(db: Session, webinar: WebinarSchema, user_id: int):
    db_webinar = WebinarModel(**webinar.model_dump(), user_id=user_id)
    db.add(db_webinar)
    db.commit()
    db.refresh(db_webinar)
    return db_webinar

def create_research_paper(db: Session, research_paper: ResearchPaperSchema, user_id: int):
    db_paper = ResearchPaperModel(
        **research_paper.model_dump(),
        user_id=user_id
    )
    db.add(db_paper)
    db.commit()
    db.refresh(db_paper)

    return db_paper





def generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return ''.join(random.choices(string.digits, k=6))

def create_otp(db: Session, user_id: int) -> OTPModel:
    otp_value = generate_otp()
    expiry_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5)  # OTP valid for 5 minutes

    otp = OTPModel(user_id=user_id, otp=otp_value, expiry=expiry_time)
    try:
        db.add(otp)
        db.commit()
        db.refresh(otp)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return otp



def get_otp(db: Session, otp_value: str) -> OTPModel:
    otp = db.query(OTPModel).filter(OTPModel.otp == otp_value, OTPModel.used == False).first()
    
    if otp is None:
        raise HTTPException(status_code=404, detail="OTP not found or already used")

    current_time = datetime.datetime.now(datetime.timezone.utc)
    if otp.expiry.tzinfo is None:
        otp_expiry_time = otp.expiry.replace(tzinfo=datetime.timezone.utc)
    else:
        otp_expiry_time = otp.expiry


    if otp_expiry_time  < current_time:
        raise HTTPException(status_code=400, detail="OTP has expired")

    return otp



def delete_otp(db: Session, otp_id: int):
    otp = db.query(OTPModel).filter(OTPModel.id == otp_id).first()

    if otp is None:
        raise HTTPException(status_code=404, detail="OTP not found")

    try:
        db.delete(otp)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting OTP: {str(e)}")



def update_user_password(db: Session, user_id: int, new_password: str):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    hashed_password = hash_password(new_password)
    user.hashed_password = hashed_password
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating password: {str(e)}")
