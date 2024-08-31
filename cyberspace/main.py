from datetime import datetime, date
import os
from typing import Optional
from fastapi import FastAPI, Depends, Form, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from pydantic import EmailStr
from sqlalchemy.orm import Session
from service import add_custom_cors_middleware, save_pdf, send_congratulation_email, send_otp_email
from database import SessionLocal, engine
from models import Base, VirtualInternship, Seminar, Webinar, ResearchPaper
import schemas, crud





app = FastAPI()

add_custom_cors_middleware(app)

Base.metadata.create_all(bind=engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

app.mount("/images", StaticFiles(directory="images"), name="images")

UPLOAD_DIRECTORY = "./uploads/papers/"

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        # Use the token to get user details
        user = crud.get_user_profile(db, token)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    


@app.post("/users/", response_model=schemas.User)
async def create_user(
    background_tasks: BackgroundTasks,
    first_name: str = Form(...),
    last_name: str = Form(...),
    email_id: EmailStr = Form(...),
    mobile_number: str = Form(...),
    college_name: str = Form(...),
    password: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    try:
        user_create = schemas.UserCreate(
            first_name=first_name,
            last_name=last_name,
            email_id=email_id,
            mobile_number=mobile_number,
            college_name=college_name,
            password=password
        )
        created_user = crud.create_user(db=db, user=user_create, image=image)

        # Send the email in the background
        background_tasks.add_task(send_congratulation_email, email_id, first_name)

        return created_user
    except HTTPException as http_error:
        raise http_error
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/login", response_model=schemas.Token)
def login(
    login: schemas.Login,
    db: Session = Depends(get_db)
):
    try:
        user = crud.authenticate_user(db, login.username, login.password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        access_token = crud.create_access_token(data={"sub": user.id})
        return {"access_token": access_token, "token_type": "bearer"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    


@app.post("/forgot-password/")
def forgot_password(
    request: schemas.EmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    try:
        email = request.email
        print(email)
        user = crud.get_user_by_email(db, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        otp = crud.create_otp(db, user.id)  # Create OTP and return the OTP value
        background_tasks.add_task(send_otp_email, email, otp.otp)
        
        return {"message": "OTP sent"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    
    
@app.post("/reset-password/")
def reset_password(
    reset_password_request: schemas.ResetPassword,
    db: Session = Depends(get_db)
):
    try:
        otp = crud.get_otp(db, otp_value=reset_password_request.otp)
        if not otp:
            raise HTTPException(status_code=400, detail="Invalid or expired OTP")
        
        if reset_password_request.new_password != reset_password_request.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        
        user = crud.get_user(db, otp.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        crud.update_user_password(db, user.id, reset_password_request.new_password)
        crud.delete_otp(db, otp.id)  # Assuming delete_otp is used here
        
        return {"message": "Password reset successful"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


# @app.get("/users/{user_id}", response_model=schemas.User)
# def read_user(
#     user_id: int,
#     db: Session = Depends(get_db),
#     user: schemas.User = Depends(get_current_user)  # Authentication applied
# ):
#     try:
#         db_user = crud.get_user(db, user_id)
#         if db_user is None:
#             raise HTTPException(status_code=404, detail="User not found")
#         return db_user
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")



@app.get("/user/profile", response_model=schemas.UserProfile)
def get_user_profile(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        user = crud.get_user_profile(db, token)
        if user is None:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Retrieve counts
        virtual_internships_count = db.query(VirtualInternship).filter(VirtualInternship.user_id == user.id).count()
        seminars_count = db.query(Seminar).filter(Seminar.user_id == user.id).count()
        webinars_count = db.query(Webinar).filter(Webinar.user_id == user.id).count()
        # research_papers_count = db.query(ResearchPaper).filter(ResearchPaper.user_id == user.id).count()

       
        # Create and return the UserProfile response model
        user_profile = schemas.UserProfile(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email_id=user.email_id,
            mobile_number=user.mobile_number,
            college_name=user.college_name,
            image_filename=user.image_filename,
            virtual_internships_count=virtual_internships_count,
            seminars_count=seminars_count,
            webinars_count=webinars_count,
            research_papers_count= 0     #research_papers_count
        )
        return user_profile

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")




@app.post("/virtualInternship/", response_model=schemas.VirtualInternship)
async def register_virtual_internship_user(
    first_name: str = Form(...),
    last_name: Optional[str] = Form(None),
    email_id: EmailStr = Form(...),
    phone_number: str = Form(...),
    address: str = Form(...),
    highest_qualification: str = Form(...),
    field_of_study: str = Form(...),
    skills_and_strengths: str = Form(...),
    experience: str = Form(...),
    available_start_date: str = Form(...),  # Use str to receive date
    preferred_internship: str = Form(...),
    additional_info: Optional[str] = Form(None),  # Optional field
    db: Session = Depends(get_db),
    dbuser: schemas.User = Depends(get_current_user)  # Authentication applied
):
    try:
        # Convert available_start_date to date
        try:
            available_start_date = datetime.strptime(available_start_date, '%d-%m-%Y').date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use 'dd-mm-yyyy'.")

        # Create VirtualInternship object
        virtual_internship = schemas.VirtualInternship(
            first_name=first_name,
            last_name=last_name,
            email_id=email_id,
            phone_number=phone_number,
            address=address,
            highest_qualification=highest_qualification,
            field_of_study=field_of_study,
            skills_and_strengths=skills_and_strengths,
            experience=experience,
            available_start_date=available_start_date,
            preferred_internship=preferred_internship,
            additional_info=additional_info
        )
        
        # Register the virtual internship user
        registered_user = crud.create_virtual_internship(db=db,  internship=virtual_internship, user_id=dbuser.id )
        if not registered_user:
            raise HTTPException(status_code=400, detail="Failed to register virtual internship user")
        
        return registered_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    


@app.post("/seminar/")
def create_seminar(
    first_name: str = Form(...),
    last_name: Optional[str] = Form(None),
    email_id: EmailStr = Form(...),
    phone_number: str = Form(...),
    course: str = Form(...),
    year_of_study: str = Form(...),
    seminar_topic: str = Form(...),
    additional_comments: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    dbuser: schemas.User = Depends(get_current_user)  # Authentication applied
):
    try:
        seminar = schemas.Seminar(
            first_name=first_name,
            last_name=last_name,
            email_id=email_id,
            phone_number=phone_number,
            course=course,
            year_of_study=year_of_study,
            seminar_topic=seminar_topic,
            additional_comments=additional_comments
        )
        created_seminar = crud.create_seminar(db=db, seminar=seminar, user_id=dbuser.id)
        return created_seminar
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/webinar/")
def create_webinar(
    first_name: str = Form(...),
    last_name: Optional[str] = Form(None),
    email_id: EmailStr = Form(...),
    phone_number: str = Form(...),
    course: str = Form(...),
    year_of_study: str = Form(...),
    webinar_topic: str = Form(...),
    additional_comments: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    dbuser: schemas.User = Depends(get_current_user)  # Authentication applied
):
    try:
        webinar = schemas.Webinar(
            first_name=first_name,
            last_name=last_name,
            email_id=email_id,
            phone_number=phone_number,
            course=course,
            year_of_study=year_of_study,
            webinar_topic=webinar_topic,
            additional_comments=additional_comments
        )
        created_webinar = crud.create_webinar(db=db, webinar=webinar, user_id=dbuser.id)
        return created_webinar
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    


@app.post("/research-paper/")
def create_research_paper(
    first_name: str = Form(...),
    last_name: Optional[str] = Form(None),
    email_id: EmailStr = Form(...),
    phone_number: str = Form(...),
    student_id: str = Form(...),
    paper_title: str = Form(...),
    abstract: str = Form(...),
    keywords: str = Form(...),
    paper_category: str = Form(...),
    paper_pdf: UploadFile = File(...),  # Handling PDF upload
    db: Session = Depends(get_db),
    dbuser: schemas.User = Depends(get_current_user) 
):
    try:
        # Save the uploaded PDF using the save_pdf function
        pdf_filename = save_pdf(paper_pdf)
        # Create the research paper object
        research_paper = schemas.ResearchPaper(
            first_name=first_name,
            last_name=last_name,
            email_id=email_id,
            phone_number=phone_number,
            student_id=student_id,
            paper_title=paper_title,
            abstract=abstract,
            keywords=keywords,
            paper_category=paper_category,
            paper_pdf=pdf_filename  # Store the unique filename in the schema
        )

        # Call the CRUD function to save the research paper in the database
        created_research_paper = crud.create_research_paper(db=db, research_paper=research_paper, user_id= dbuser.id )

        return created_research_paper
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

