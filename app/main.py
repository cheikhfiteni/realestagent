# Basic structure for app/main.py
from fastapi import BackgroundTasks, FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.logic import run_job as run_job_logic
from app.services.authentication import ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, router as auth_router, get_current_user
from pydantic import BaseModel
from typing import Dict, Optional, List
from datetime import datetime
from sqlalchemy import text
from app.db.database import (
    engine, get_user_jobs, get_job_with_listings, 
    create_job_template, create_job, get_pending_jobs
)
from app.models.models import User
from starlette.middleware.sessions import SessionMiddleware
from uuid import UUID
from functools import wraps

from app.config import FRONTEND_URL

class JobInput(BaseModel):
    name: str
    min_bedrooms: Optional[int] = 4
    min_square_feet: Optional[int] = 1000  
    min_bathrooms: Optional[float] = 2.0
    target_price_bedroom: Optional[int] = 2000
    criteria: Optional[str] = None

class JobStubOutput(BaseModel):
    id: UUID
    name: str
    last_updated: datetime

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

async def run_single_job(job_id: UUID):
    try:
        # Run the job using template config
        await run_job_logic(job_id)
    except Exception as e:
        print(f"Error running job {job_id}: {str(e)}")

def scheduled_task(interval_minutes: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        # Add job to scheduler
        scheduler.add_job(wrapper, 'interval', minutes=interval_minutes)
        return wrapper
    return decorator

@scheduled_task(interval_minutes=1)
async def run_scheduled_jobs_async():
    pending_jobs = await get_pending_jobs()
    for job in pending_jobs:
        await run_single_job(job.id)

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

    print("\033[95m" + str([{"id": job.id, "name": job.name, "last_updated": job.updated_at} for job in jobs]) + "\033[0m")
    job_stubs = [JobStubOutput(id=job.id, name=job.name, last_updated=job.updated_at or job.created_at) for job in jobs]
    return job_stubs

@app.get("/jobs/{job_id}", response_model=List[ListingOutput])
async def get_job(job_id: UUID, current_user: User = Depends(get_current_user)):
    """Get all scored listings for a specific job"""
    listings = await get_job_with_listings(job_id, current_user.id)
    if listings is None:
        raise HTTPException(status_code=404, detail="Job not found or unauthorized")
    return listings

@app.post("/jobs/add")
async def add_job(job_input: JobInput, current_user: User = Depends(get_current_user), background_tasks: BackgroundTasks = BackgroundTasks()):
    """Create a new job from input template"""
    try:
        # Create template
        template = await create_job_template(current_user.id, job_input.dict())
        
        # Create job
        job = await create_job(current_user.id, template.id, job_input.name)
        
        # Run initial job
        background_tasks.add_task(run_single_job, job.id)
        
        return {"status": "created", "job_id": job.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
