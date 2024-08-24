from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email_id = Column(String(100), unique=True)
    mobile_number = Column(String(20), unique=True)
    college_name = Column(String(50))
    hashed_password = Column(String(255))
    image_filename = Column(String(100), nullable=True)

    virtual_internships = relationship("VirtualInternship", back_populates="user")
    seminars = relationship("Seminar", back_populates="user")
    webinars = relationship("Webinar", back_populates="user")
    research_papers = relationship("ResearchPaper", back_populates="user")
    otps = relationship("OTP", back_populates="user")

class VirtualInternship(Base):
    __tablename__ = "virtual_internships"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    first_name = Column(String(50))
    last_name = Column(String(50))
    email_id = Column(String(100))
    phone_number = Column(String(20))
    address = Column(String(100))
    highest_qualification = Column(String(50))
    field_of_study = Column(String(50))
    skills_and_strengths = Column(String(300))
    experience = Column(String(300))
    available_start_date = Column(DateTime)
    preferred_internship = Column(String(100))
    additional_info = Column(String(300))

    user = relationship("User", back_populates="virtual_internships")

class Seminar(Base):
    __tablename__ = "seminars"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    first_name = Column(String(50))
    last_name = Column(String(50))
    email_id = Column(String(100))
    phone_number = Column(String(20))
    course = Column(String(50))
    year_of_study = Column(String(10))
    seminar_topic = Column(String(300))
    additional_comments = Column(String(300))

    user = relationship("User", back_populates="seminars")

class Webinar(Base):
    __tablename__ = "webinars"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    first_name = Column(String(50))
    last_name = Column(String(50))
    email_id = Column(String(100))
    phone_number = Column(String(20))
    course = Column(String(50))
    year_of_study = Column(String(10))
    webinar_topic = Column(String(300))
    additional_comments = Column(String(300))

    user = relationship("User", back_populates="webinars")

class ResearchPaper(Base):
    __tablename__ = "research_papers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    first_name = Column(String(50))
    last_name = Column(String(50))
    email_id = Column(String(100))
    phone_number = Column(String(20))
    student_id = Column(String(50))
    paper_title = Column(String(300))
    abstract = Column(String(1000))
    keywords = Column(String(300))
    paper_category = Column(String(100))
    paper_pdf = Column(String(100))  # Path or filename for the uploaded PDF

    user = relationship("User", back_populates="research_papers")

class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    otp = Column(String(6))
    expiry = Column(DateTime(timezone=True))  # Ensure timezone-aware
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used = Column(Boolean, default=False)

    user = relationship("User", back_populates="otps")