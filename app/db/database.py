import hashlib
from app.models.models import engine, Listing, Job, JobTemplate, JobListingScore
from sqlalchemy.orm import sessionmaker, Session
from app.config import DATABASE_URL, NO_IMAGE_URL
from sqlalchemy import create_engine, select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import contextmanager, asynccontextmanager
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
from uuid import UUID
from sqlalchemy import and_
from sqlalchemy.orm import selectinload

# Sync SQLAlchemy engine for migrations and model creation
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

# Async engine
async_engine = create_async_engine(
    DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://').replace("?sslmode=", "?ssl=")
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
    

async def save_new_listings_to_db(listings: list[Listing]) -> list[Listing]:
    saved_listings = []
    async with get_async_db() as session:
        columns = [
            'hash', 'title', 'bedrooms', 'bathrooms', 'square_footage',
            'post_id', 'description', 'price', 'location', 'neighborhood',
            'image_urls', 'link'
        ]

        for listing in listings:
            result = await session.execute(
                select(Listing).where(Listing.hash == listing.hash)
            )
            existing = result.scalar_one_or_none()

            if not existing:
                listing_data = {
                    column: getattr(listing, column)
                    for column in columns
                }
                
                new_listing = Listing(
                    **listing_data
                )
                session.add(new_listing)
                await session.commit()
                await session.refresh(new_listing)
                saved_listings.append(new_listing)
            else:
                saved_listings.append(existing)
    
    return saved_listings

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

async def create_job_template(user_id: UUID, job_input: dict) -> JobTemplate:
    async with get_async_db() as session:
        template_data = {
            k: v for k, v in job_input.items() 
            if k in ['min_bedrooms', 'min_square_feet', 'min_bathrooms', 'target_price_bedroom', 'criteria',
                    'location', 'zipcode', 'search_distance_miles']
        }
        template = JobTemplate(
            user_id=user_id,
            **template_data
        )
        session.add(template)
        await session.commit()
        await session.refresh(template)
        return template

async def create_job(user_id: UUID, template_id: UUID, name: str) -> Job:
    async with get_async_db() as session:
        now = datetime.now()
        job = Job(
            user_id=user_id,
            template_id=template_id,
            name=name,
            created_at=now, 
            updated_at=now
        )
        session.add(job)
        await session.commit()
        await session.refresh(job)
        return job

async def get_user_jobs(user_id: UUID):
    # Subquery to count listings per job
    listing_count = (
        select(func.count(JobListingScore.listing_id))
        .where(JobListingScore.job_id == Job.id)
        .scalar_subquery()
        .label('listing_count')
    )

    # Subquery to get the highest scored listing's image for each job
    latest_listing = (
        select(Listing.image_urls)
        .join(JobListingScore, JobListingScore.listing_id == Listing.id)
        .where(JobListingScore.job_id == Job.id)
        .order_by(JobListingScore.score.desc())
        .limit(1)
        .scalar_subquery()
        .label('best_listing_images')
    )

    query = (
        select(Job, listing_count, latest_listing)
        .where(Job.user_id == user_id)
        .order_by(Job.updated_at.desc())
    )
    
    async with get_async_db() as session:
        result = await session.execute(query)
        jobs_data = []
        for job, count, images in result.all():
            image_urls = json.loads(images) if images else []
            jobs_data.append((job, count, image_urls[0] if image_urls else NO_IMAGE_URL))
        return jobs_data

async def get_job_with_listings(job_id: UUID, user_id: UUID) -> Optional[Dict]:
    """Get a job's listings with their scores."""
    async with get_async_db() as session:
        # Get job and verify user
        job = await session.get(Job, job_id)
        if not job or job.user_id != user_id:
            return None
            
        # Get all listings with scores in a single query
        result = await session.execute(
            select(Listing, JobListingScore)
            .join(JobListingScore, JobListingScore.listing_id == Listing.id)
            .where(JobListingScore.job_id == job_id)
        )
        listing_scores = result.all()
        
        if not listing_scores:
            return []
            
        # Format response
        formatted_listings = []
        for listing, score in listing_scores:
            image_urls = json.loads(listing.image_urls) if listing.image_urls else []
            formatted_listings.append({
                "id": listing.id,
                "title": listing.title,
                "cover_image_url": image_urls[0] if image_urls else NO_IMAGE_URL,
                "location": listing.location,
                "cost": listing.price,
                "bedrooms": listing.bedrooms,
                "bathrooms": listing.bathrooms,
                "square_footage": listing.square_footage,
                "score": score.score,
                "trace": score.trace,
                "link": listing.link
            })
        
        return formatted_listings

async def update_job_listing_score(job_id: UUID, listing_id: UUID, score: float, trace: str):
    """Update or create a score for a specific listing in a job."""
    async with get_async_db() as session:
        # Get or create job listing score
        score_obj = await session.get(JobListingScore, {'job_id': job_id, 'listing_id': listing_id})
        if not score_obj:
            score_obj = JobListingScore(
                job_id=job_id,
                listing_id=listing_id,
                score=score,
                trace=trace
            )
            session.add(score_obj)
        else:
            score_obj.score = score
            score_obj.trace = trace
            score_obj.updated_at = datetime.now()
        
        await session.commit()
        return score_obj

async def get_pending_jobs() -> List[Job]:
    """Get jobs that haven't been updated in 24 hours"""
    async with get_async_db() as session:
        one_day_ago = datetime.now() - timedelta(days=1)
        result = await session.execute(
            select(Job).where(Job.updated_at <= one_day_ago)
        )
        return result.scalars().all()
    
async def get_next_pending_job() -> Optional[Job]:
    """Get the oldest job that hasn't been updated in 24 hours"""
    async with get_async_db() as session:
        one_day_ago = datetime.now() - timedelta(days=1)
        result = await session.execute(
            select(Job).where(Job.updated_at <= one_day_ago).order_by(Job.updated_at).limit(1)
        )
        return result.scalars().first()

async def get_listing_by_id(listing_id: UUID) -> Optional[Listing]:
    """Get a listing by its UUID."""
    async with get_async_db() as session:
        result = await session.get(Listing, listing_id)
        return result

async def get_job_listing_scores(job_id: UUID) -> List[JobListingScore]:
    """Get all listing scores for a specific job."""
    async with get_async_db() as session:
        result = await session.execute(
            select(JobListingScore).where(JobListingScore.job_id == job_id)
        )
        return result.scalars().all()

async def get_listing_id_by_hash(listing_hashes: List[str]) -> List[UUID]:
    """Get listing IDs by their hashes."""
    async with get_async_db() as session:
        result = await session.execute(
            select(Listing.id).where(Listing.hash.in_(listing_hashes))
        )
        return result.scalars().all()
        

async def filter_listing_ids_on_job(job_id: UUID, listing_ids: List[UUID]) -> List[UUID]:
    """Get listing IDs that already have a relationship with the given job."""
    async with get_async_db() as session:
        result = await session.execute(
            select(JobListingScore.listing_id).where(
                and_(
                    JobListingScore.job_id == job_id,
                    JobListingScore.listing_id.in_(listing_ids)
                )
            )
        )
        return result.scalars().all()

