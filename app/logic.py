import asyncio
from functools import wraps
from typing import List, Set
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.evaluator import evaluate_listing_aesthetics, evaluate_listing_hueristics
from app.models.models import Listing, Job
from app.db.database import (
    filter_listing_ids_on_job, get_async_db, get_listing_id_by_hash, get_stored_listing_hashes, save_new_listings_to_db,
    update_job_listing_score, get_listing_by_id, get_job_listing_scores
)

from app.core.base_scraper import ScrapingConfig
from app.core.craiglist_scraper import CraigslistScraper
from app.services.celery_app import celery
BATCH_SIZE = 5
SLEEP_TIME = 0.2

async def batch_database_save(upsert_listings: List[Listing], job_id: UUID, session: AsyncSession) -> List[Listing]:
    saved_listings = await save_new_listings_to_db(upsert_listings)
    for listing in saved_listings:
        await update_job_listing_score(job_id, listing.id, 0, "")
    return []

async def batch_memoized_score_update(job_id: UUID, listing_hashes: List[str], session: AsyncSession) -> None:
    """Update job-listing relationships for existing listings."""
    listing_ids = await get_listing_id_by_hash(listing_hashes)
    existing_ids = await filter_listing_ids_on_job(job_id, listing_ids)
    for li in listing_ids:
        if li not in existing_ids:
            await update_job_listing_score(job_id, li, 0, "")

async def scrape_listings(job: Job, session: AsyncSession):
    print(f"[DEBUG] Starting scrape_listings for job {job.id}")
    print(f"[DEBUG] Job template: {job.template}")
    config = ScrapingConfig.from_job_template(job.template)
    print(f"[DEBUG] Created scraping config: min_price={config.min_price}, max_price={config.max_price}, min_bedrooms={config.min_bedrooms}")
    
    stored_hashes = get_stored_listing_hashes()
    print(f"[DEBUG] Retrieved {len(stored_hashes)} stored listing hashes")
    
    print(f"[DEBUG] Initializing CraigslistScraper for job {job.id}")
    with CraigslistScraper.create(config) as scraper:
        upsert_listings = []
        listing_hashes_from_scrape = []
        print(f"[DEBUG] Starting scraping loop for job {job.id}")
        
        async for scrape_output in scraper.scrape():
            if isinstance(scrape_output, str):  # It's a hash
                listing_hashes_from_scrape.append(scrape_output)
            else:  # It's a new listing
                if isinstance(scrape_output, Listing) and scrape_output.hash not in stored_hashes:
                    upsert_listings.append(scrape_output)
                
            if len(upsert_listings) >= BATCH_SIZE:
                upsert_listings = await batch_database_save(upsert_listings, job.id, session)
                    
        if upsert_listings:
            upsert_listings = await batch_database_save(upsert_listings, job.id, session)
            
        if listing_hashes_from_scrape:
            await batch_memoized_score_update(job.id, listing_hashes_from_scrape, session)

async def evaluate_job_listings(job: Job, session: AsyncSession):
    """Evaluate listings for a specific job using its template criteria."""
    listing_scores = await get_job_listing_scores(job.id)
    
    print(f"\033[33mEvaluating listings for job: {job.name}")
    print(f"Found {len(listing_scores)} listings to evaluate\033[0m")
    
    for score in listing_scores:
        if score.score == 0:
            try:
                listing = await get_listing_by_id(score.listing_id)
                if not listing:
                    print(f"Listing {score.listing_id} not found for evaluation.")
                    continue

                hueristic_score, hueristic_trace = evaluate_listing_hueristics(listing)
                aesthetic_score, aesthetic_trace = evaluate_listing_aesthetics(listing)
                total_score = hueristic_score + aesthetic_score
                total_trace = f"{hueristic_trace} | {aesthetic_trace}"
                
                await update_job_listing_score(job.id, listing.id, total_score, total_trace)
                
            except Exception as e:
                print(f"Error evaluating listing {score.listing_id}: {str(e)}")
                continue

# def async_task(app=None, *args, **kwargs):
#     """Decorator to properly handle async tasks with Celery."""
#     def decorator(func):
#         @app.task(*args, **kwargs)
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             # Get the event loop or create one if it doesn't exist
#             try:
#                 loop = asyncio.get_event_loop()
#             except RuntimeError:
#                 loop = asyncio.new_event_loop()
#                 asyncio.set_event_loop(loop)
            
#             # Run the coroutine and return its result
#             return loop.run_until_complete(func(*args, **kwargs))
#         return wrapper
#     return decorator


# @async_task(app=celery, bind=True, max_retries=1)
@celery.task(bind=True, max_retries=1)
def run_single_job(self, job_id: UUID):
    """Run a complete job cycle - scraping and evaluation."""
    import asyncio
    
    async def _run_job():
        async with get_async_db() as session:
            job = await session.get(Job, job_id)
            if not job:
                print(f"ERROR: Job {job_id} not found")
                raise ValueError(f"Job {job_id} not found")
            
            print(f"Running scrape listings for job {job_id}")
            await scrape_listings(job, session)
            
            print(f"Running evaluate job listings for job {job_id}")
            await evaluate_job_listings(job, session)

    asyncio.run(_run_job())

async def test_just_evaluation(job_id: UUID):
    async with get_async_db() as session:
        job = await session.get(Job, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        await evaluate_job_listings(job, session)

if __name__ == "__main__":
    from uuid import UUID 

    class MockTask:
        def __init__(self, task_id=None):
            self.request = {'id': task_id or 'local-test-id'}

    mock_task_instance = MockTask()
    
    job_id_to_run = UUID('031cbf19-3254-46e0-9d61-9b37e14255a5')

    print(f"Attempting to run job {job_id_to_run} locally...")
    try:
        run_single_job(mock_task_instance, job_id_to_run)
        print(f"Job {job_id_to_run} finished.")
    except ValueError as e:
        print(f"Error during local job run: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")