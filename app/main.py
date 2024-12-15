# Basic structure for app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from app.logic import run_job as run_job_logic
from app.services.authentication import router as auth_router
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime
import uuid
from sqlalchemy import text
from app.db.database import engine

class JobInput(BaseModel):
    min_bedrooms: int | None = 4
    min_square_feet: int | None = 1000  
    min_bathrooms: float | None = 2.0
    target_price_bedroom: int | None = 2000
    criteria: str | None = None

class JobResult(BaseModel):
    job_id: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error: Optional[str]

app = FastAPI()
app.include_router(auth_router, prefix="/auth", tags=["authentication"])
scheduler = BackgroundScheduler()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,                    # Important for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job queue and results store
job_queue: Dict[str, JobInput] = {}
job_results: Dict[str, JobResult] = {}

@app.on_event("startup")
async def startup_event():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

# Schedule jobs
@scheduler.scheduled_job('interval', hours=24)
def run_scheduled_jobs():
    for job_id, job_input in job_queue.items():
        try:
            # Update job status
            job_results[job_id].status = "running"
            job_results[job_id].started_at = datetime.now()
            
            # Run the job
            run_job_logic()
            
            # Update completion status
            job_results[job_id].status = "completed"
            job_results[job_id].completed_at = datetime.now()
            
            # Remove from queue after successful completion
            del job_queue[job_id]
            
        except Exception as e:
            job_results[job_id].status = "failed"
            job_results[job_id].error = str(e)
            job_results[job_id].completed_at = datetime.now()

# API Endpoints

@app.get("/")
async def root():
    return {"status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    if job_id not in job_results:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_results[job_id]

@app.post("/jobs/add")
async def add_job(job_input: JobInput):
    job_id = str(uuid.uuid4())
    
    # Add to queue
    job_queue[job_id] = job_input
    
    # Initialize result object
    job_results[job_id] = JobResult(
        job_id=job_id,
        status="queued",
        started_at=None,
        completed_at=None,
        error=None
    )
    
    return {"status": "queued", "job_id": job_id}

@app.get("/db-health")
async def database_health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
