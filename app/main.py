# Basic structure for app/main.py
from asyncio import Lock
from fastapi import BackgroundTasks, FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.logic import run_single_job, test_just_evaluation
from app.services.authentication import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, router as auth_router, get_current_user, send_invitation_email_stub
from pydantic import BaseModel
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy import text
from app.db.database import (
    engine, get_next_pending_job, get_user_jobs, get_job_with_listings, 
    create_job_template, create_job,
    get_user_by_email, create_invited_user, add_user_to_job_access, get_job_by_id
)
from app.models.models import User
from starlette.middleware.sessions import SessionMiddleware
from uuid import UUID
from functools import wraps

from app.config import FRONTEND_URL
import httpx
class JobInput(BaseModel):
    name: str
    min_bedrooms: Optional[int] = 4
    min_square_feet: Optional[int] = 1000  
    min_bathrooms: Optional[float] = 2.0
    target_price_bedroom: Optional[int] = 2000
    criteria: Optional[str] = None
    location: Optional[str] = None
    zipcode: Optional[str] = None
    search_distance_miles: Optional[float] = 10.0

class InviteInput(BaseModel):
    email: str

class JobStubOutput(BaseModel):
    id: UUID
    name: str
    last_updated: datetime
    listing_count: int
    cover_image_url: str

class ListingOutput(BaseModel):
    id: UUID
    title: str
    cover_image_url: str
    location: str
    cost: int
    bedrooms: int
    bathrooms: float
    square_footage: int
    score: float
    trace: str
    link: str

app = FastAPI()
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
scheduler = AsyncIOScheduler(
    job_defaults={
        'coalesce': True,
        'max_instances': 1
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
        SessionMiddleware,
        secret_key=SECRET_KEY,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60
)

@app.on_event("startup")
async def startup_event():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

def scheduled_task(interval_minutes: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        # Add job to scheduler
        scheduler.add_job(wrapper, 'interval', minutes=interval_minutes)
        return wrapper
    return decorator

_job_lock = Lock()

@scheduled_task(interval_minutes=1)
async def run_scheduled_jobs_async():
    if not _job_lock.locked():
        async with _job_lock:
            if (pending_job := await get_next_pending_job()):
                run_single_job.delay(pending_job.id)

@app.get("/test-evaluation")
async def run_test_evaluation():
    """Run evaluation for test job repeatedly"""
    test_job_id = UUID('031cbf19-3254-46e0-9d61-9b37e14255a5')
    try:
        await test_just_evaluation(test_job_id)
        return {"status": "success"}
    except Exception as e:
        print(f"Error running test evaluation: {str(e)}")
        return {"status": "error", "message": str(e)}

# API Endpoints

@app.get("/")
async def root():
    return {"status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/jobs", response_model=List[JobStubOutput])
async def get_job_ids(current_user: User = Depends(get_current_user)):
    """Get all job IDs for the current user"""
    jobs = await get_user_jobs(current_user.id)
    job_stubs = [
        JobStubOutput(
            id=job.id,
            name=job.name,
            last_updated=job.updated_at or job.created_at,
            listing_count=listing_count,
            cover_image_url=cover_image_url
        ) for job, listing_count, cover_image_url in jobs
    ]
    return job_stubs

@app.get("/jobs/{job_id}", response_model=List[ListingOutput])
async def get_job(job_id: UUID, current_user: User = Depends(get_current_user)):
    """Get all scored listings for a specific job"""
    listings = await get_job_with_listings(job_id, current_user.id)
    if listings is None:
        raise HTTPException(status_code=404, detail="Job not found or unauthorized")
    return listings

@app.post("/jobs/add")
async def add_job(job_input: JobInput, current_user: User = Depends(get_current_user)):
    """Create a new job from input template"""
    try:
        template = await create_job_template(current_user.id, job_input.dict())
        job = await create_job(current_user.id, template.id, job_input.name)
        
        run_single_job.delay(job.id)
        
        return {"status": "created", "job_id": job.id}
    except Exception as e:
        print(f"\033[91mError creating job: {str(e)}\033[0m")  # Red color for error logging
        if isinstance(e, ValueError):
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create job: {str(e)}"
        )

@app.post("/jobs/{job_id}/invite")
async def invite_user_to_job(
    job_id: UUID,
    invite_input: InviteInput,
    current_user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    job = await get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have permission to invite users to this job.")

    target_email = invite_input.email.lower().strip()
    if not target_email:
        raise HTTPException(status_code=400, detail="Email cannot be empty.")
    if target_email == current_user.email:
        raise HTTPException(status_code=400, detail="You cannot invite yourself to a job.")

    invited_user = await get_user_by_email(target_email)
    is_new_user_scenario = False

    if not invited_user:
        invited_user = await create_invited_user(target_email)
        is_new_user_scenario = True
    elif invited_user.account_status == 'invited' and not invited_user.is_active:
        is_new_user_scenario = True

    access_newly_granted = await add_user_to_job_access(invited_user.id, job_id)

    if not access_newly_granted:
        return {"status": "info", "message": f"User {target_email} already has access to this job."}

    background_tasks.add_task(
        send_invitation_email_stub,
        to_email=target_email,
        job_name=job.name,
        invited_by_email=current_user.email
    )
    
    if is_new_user_scenario:
        return {"status": "success", "message": f"Invitation sent to {target_email}. They will need to complete their account registration."}
    else:
        return {"status": "success", "message": f"Job '{job.name}' has been shared with {target_email}."}

@app.get("/db-health")
async def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")

@app.get("/changelog")
async def get_changelog():
    return [
        {
            "id": 1,
            "date": "2024-01-15",
            "title": "Initial Release",
            "description": "Launched the first version of ApartmentFinder with basic search functionality."
        },
        {
            "id": 2, 
            "date": "2024-01-20",
            "title": "Search Improvements",
            "description": "Added filters for bedrooms, bathrooms and square footage. Improved search accuracy."
        },
        {
            "id": 3,
            "date": "2024-01-25", 
            "title": "UI Updates",
            "description": "Refreshed the user interface with a modern design. Added dark mode support."
        }
    ]

@app.get("/craiglist/hostnames")
async def get_craiglist_hostnames():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://reference.craigslist.org/Areas")
        data = response.json()
        return [area["Hostname"] for area in data]