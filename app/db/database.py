import hashlib
from app.models.models import engine, Listing, Job, JobTemplate, JobListingScore, User, job_access
from sqlalchemy.orm import sessionmaker, Session
from app.config import DATABASE_URL, NO_IMAGE_URL
from sqlalchemy import create_engine, select, func, or_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import selectinload, aliased, contains_eager
from contextlib import contextmanager, asynccontextmanager
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
from uuid import UUID
from sqlalchemy import and_

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
    listing_count_subquery = (
        select(func.count(JobListingScore.listing_id))
        .where(JobListingScore.job_id == Job.id)
        .correlate(Job)
        .scalar_subquery()
        .label("listing_count")
    )

    latest_listing_image_subquery = (
        select(Listing.image_urls)
        .join(JobListingScore, JobListingScore.listing_id == Listing.id)
        .where(JobListingScore.job_id == Job.id)
        .correlate(Job)
        .order_by(JobListingScore.score.desc())
        .limit(1)
        .scalar_subquery()
        .label("best_listing_images")
    )

    jt_alias = aliased(JobTemplate, name="template_alias")

    query = (
        select(Job, listing_count_subquery, latest_listing_image_subquery)
        .join(jt_alias, Job.template_id == jt_alias.id)
        .outerjoin(job_access, job_access.c.job_id == Job.id)
        .where(
            or_(
                Job.user_id == user_id,
                job_access.c.user_id == user_id
            )
        )
        .group_by(
            Job.id,
            jt_alias.id,
            jt_alias.user_id,
            jt_alias.min_bedrooms,
            jt_alias.min_square_feet,
            jt_alias.min_bathrooms,
            jt_alias.target_price_bedroom,
            jt_alias.criteria,
            jt_alias.location,
            jt_alias.zipcode,
            jt_alias.search_distance_miles,
            jt_alias.created_at
        )
        .order_by(Job.updated_at.desc(), Job.created_at.desc())
        .options(contains_eager(Job.template, alias=jt_alias))
    )
    
    async with get_async_db() as session:
        result = await session.execute(query)
        jobs_data = []
        for job_instance, count, images in result.all():
            image_urls_list = []
            if images and isinstance(images, str):
                try:
                    loaded_images = json.loads(images)
                    if isinstance(loaded_images, list):
                        image_urls_list = loaded_images
                except json.JSONDecodeError:
                    pass
            elif isinstance(images, list):
                image_urls_list = images

            jobs_data.append((job_instance, count if count is not None else 0, image_urls_list[0] if image_urls_list else NO_IMAGE_URL))
        return jobs_data

async def get_job_with_listings(job_id: UUID, user_id: UUID) -> Optional[List[Dict]]:
    if not await check_job_access(job_id, user_id):
        return None
            
    async with get_async_db() as session:
        result = await session.execute(
            select(Listing, JobListingScore)
            .join(JobListingScore, JobListingScore.listing_id == Listing.id)
            .where(JobListingScore.job_id == job_id)
            .order_by(JobListingScore.score.desc())
        )
        listing_scores = result.all()
        
        if not listing_scores:
            return []
            
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

async def get_user_by_email(email: str) -> Optional[User]:
    async with get_async_db() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

async def create_invited_user(email: str) -> User:
    async with get_async_db() as session:
        new_user = User(email=email, account_status='invited', is_active=False)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

async def add_user_to_job_access(user_id: UUID, job_id: UUID) -> bool:
    async with get_async_db() as session:
        existing_access_result = await session.execute(
            select(job_access).where(
                and_(job_access.c.user_id == user_id, job_access.c.job_id == job_id)
            )
        )
        if existing_access_result.scalar_one_or_none():
            return False

        stmt = job_access.insert().values(user_id=user_id, job_id=job_id)
        await session.execute(stmt)
        await session.commit()
        return True

async def check_job_access(job_id: UUID, user_id: UUID) -> bool:
    async with get_async_db() as session:
        job_owner_result = await session.execute(select(Job).where(and_(Job.id == job_id, Job.user_id == user_id)))
        if job_owner_result.scalar_one_or_none():
            return True
        
        shared_access_result = await session.execute(
            select(job_access).where(
                and_(job_access.c.user_id == user_id, job_access.c.job_id == job_id)
            )
        )
        return shared_access_result.scalar_one_or_none() is not None

async def get_job_by_id(job_id: UUID) -> Optional[Job]:
    async with get_async_db() as session:
        job = await session.get(Job, job_id)
        return job

