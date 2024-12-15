import hashlib
from app.models.models import engine, Listing
from sqlalchemy.orm import sessionmaker, Session
from app.config import DATABASE_URL

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from contextlib import contextmanager, asynccontextmanager


# Sync SQLAlchemy engine for migrations and model creation
engine = create_engine(DATABASE_URL)
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
