import hashlib
from app.models.models import engine, Listing, Job, JobTemplate, User
from sqlalchemy.orm import sessionmaker, Session
from app.config import DATABASE_URL
from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import contextmanager, asynccontextmanager
from typing import List, Dict, Optional
from datetime import datetime
import json

# Sync SQLAlchemy engine for migrations and model creation
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

# Async engine
async_engine = create_async_engine(
    DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
)
AsyncSessionLocal = sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Sync context manager (keep this)
@contextmanager
def get_db_session() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# New async context manager (replaces databases usage)
@asynccontextmanager
async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def _listing_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

def get_stored_listing_hashes():
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        return {listing.hash for listing in session.query(Listing).all()}
    finally:
        session.close()
    

def save_new_listings_to_db(listings: list[Listing]):
    with get_db_session() as session:
        columns = [
            'hash', 'title', 'bedrooms', 'bathrooms', 'square_footage',
            'post_id', 'description', 'price', 'location', 'neighborhood',
            'image_urls', 'link'
        ]

        for listing in listings:
            existing = session.query(Listing).filter_by(hash=listing.hash).first()

            if not existing:
                listing_data = {
                    column: getattr(listing, column)
                    for column in columns
                }
                
                new_listing = Listing(
                    **listing_data,
                    score=0,
                    trace=""
                )
                session.add(new_listing)
                session.commit()
    
    session.close()

def get_unevaluated_listings() -> tuple[Session, list[Listing]]:
    """Get listings that haven't been evaluated yet."""
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        return session, session.query(Listing).filter(
            ((Listing.score == 0) & (Listing.trace == "")) |
            (Listing.score.is_(None)) |
            (Listing.trace.is_(None))
        ).all()
    except Exception as e:
        session.close()
        raise e

def get_top_listings(limit: int = 10) -> list[Listing]:
    """Get the top scored listings from the database."""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        return session.query(Listing)\
            .filter(Listing.score.isnot(None))\
            .order_by(Listing.score.desc())\
            .limit(limit)\
            .all()
    finally:
        session.close()

async def create_job_template(user_id: int, job_input: dict) -> JobTemplate:
    async with get_async_db() as session:
        template = JobTemplate(
            user_id=user_id,
            **job_input
        )
        session.add(template)
        await session.commit()
        await session.refresh(template)
        return template

async def create_job(user_id: int, template_id: int) -> Job:
    async with get_async_db() as session:
        job = Job(
            user_id=user_id,
            template_id=template_id,
            listing_scores={}
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

async def get_user_jobs(user_id: int) -> List[Job]:
    async with get_async_db() as session:
        result = await session.execute(
            select(Job).where(Job.user_id == user_id)
        )
        return result.scalars().all()

async def get_job_with_listings(job_id: int, user_id: int) -> Optional[Dict]:
    async with get_async_db() as session:
        # Get job and verify user
        job = await session.get(Job, job_id)
        if not job or job.user_id != user_id:
            return None
            
        # Get all listings referenced in job
        listing_ids = list(job.listing_scores.keys())
        if not listing_ids:
            return []
            
        result = await session.execute(
            select(Listing).where(Listing.id.in_(listing_ids))
        )
        listings = result.scalars().all()
        
        # Format response
        formatted_listings = []
        for listing in listings:
            score_data = job.listing_scores.get(str(listing.id), {})
            image_urls = json.loads(listing.image_urls) if listing.image_urls else []
            formatted_listings.append({
                "id": listing.id,
                "title": listing.title,
                "cover_image_url": image_urls[0] if image_urls else None,
                "location": listing.location,
                "cost": listing.price,
                "bedrooms": listing.bedrooms,
                "bathrooms": listing.bathrooms,
                "square_footage": listing.square_footage,
                "score": score_data.get("score", 0),
                "trace": score_data.get("trace", "")
            })
        
        return formatted_listings

async def update_job_listing_score(job_id: int, listing_id: int, score: float, trace: str):
    async with get_async_db() as session:
        job = await session.get(Job, job_id)
        if not job:
            return None
            
        scores = job.listing_scores or {}
        scores[str(listing_id)] = {"score": score, "trace": trace}
        job.listing_scores = scores
        job.updated_at = datetime.now()
        
        await session.commit()
        return job

async def get_pending_jobs() -> List[Job]:
    """Get jobs that haven't been updated in 24 hours"""
    async with get_async_db() as session:
        result = await session.execute(
            select(Job).where(
                (datetime.now() - Job.updated_at).days >= 1
            )
        )
        return result.scalars().all()
