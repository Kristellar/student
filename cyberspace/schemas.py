
from datetime import date
from typing import List, Optional
from fastapi import UploadFile
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email_id: EmailStr
    mobile_number: str
    college_name: str

class UserCreate(UserBase):
    password: str

    class Config:
        orm_mode = True

class User(UserBase):
    id: int
    hashed_password: str
    image_filename: Optional[str]

    class Config:
        orm_mode = True

    @property
    def profile_picture_url(self):
        if self.image_filename:
            return f"/images/{self.image_filename}"
        return None

class Login(BaseModel):
    username: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class EmailRequest(BaseModel):
    email: EmailStr

class ResetPassword(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    confirm_password: str

class Message(BaseModel):
    message: str

class VirtualInternship(BaseModel):
    first_name: str
    last_name: str
    email_id: EmailStr
    phone_number: str
    address: str
    highest_qualification: str
    field_of_study: str
    skills_and_strengths: str
    experience: str
    available_start_date: date
    preferred_internship: str
    additional_info: Optional[str] = None

    class Config:
        orm_mode = True

class Seminar(BaseModel):
    first_name: str
    last_name: str
    email_id: EmailStr
    phone_number: str
    course: str
    year_of_study: str
    seminar_topic: str
    additional_comments: Optional[str]

    class Config:
        orm_mode = True

class Webinar(BaseModel):
    first_name: str
    last_name: str
    email_id: EmailStr
    phone_number: str
    course: str
    year_of_study: str
    webinar_topic: str
    additional_comments: Optional[str]

    class Config:
        orm_mode = True

class ResearchPaper(BaseModel):
    first_name: str
    last_name: str
    email_id: EmailStr
    phone_number: str
    student_id: str
    paper_title: str
    abstract: str
    keywords: str
    paper_category: str
    paper_pdf: Optional[str]  # This will be the filename or path

    class Config:
        orm_mode = True

class PasswordResetRequest(BaseModel):
    email_id: EmailStr

class UserProfile(BaseModel):
    id: int
    first_name: str
    last_name: str
    email_id: str
    mobile_number: str
    college_name: str
    image_filename: Optional[str] = None
    virtual_internships_count: int
    seminars_count: int
    webinars_count: int
    research_papers_count: int

    class Config:
        orm_mode = True
