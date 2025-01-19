from typing import List
from uuid import UUID
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

async def batch_database_save(upsert_listings: List[Listing], job_id: UUID) -> List[Listing]:
    saved_listings = await save_new_listings_to_db(upsert_listings)
    for listing in saved_listings:
        await update_job_listing_score(job_id, listing.id, 0, "")
    return []

async def batch_memoized_score_update(job_id: UUID, listing_hashes: List[str]) -> None:
    """Update job-listing relationships for existing listings."""
    listing_ids = await get_listing_id_by_hash(listing_hashes)
    existing_ids = await filter_listing_ids_on_job(job_id, listing_ids)
    for li in listing_ids:
        if li not in existing_ids:
            await update_job_listing_score(job_id, li, 0, "")

async def scrape_listings(job: Job):
    print(f"[DEBUG] Starting scrape_listings for job {job.id}")
    print(f"[DEBUG] Job template: {job.template}")
    config = ScrapingConfig.from_job_template(job.template)
    print(f"[DEBUG] Created scraping config: min_price={config.min_price}, max_price={config.max_price}, min_bedrooms={config.min_bedrooms}")
    
    stored_hashes = get_stored_listing_hashes()
    print(f"[DEBUG] Retrieved {len(stored_hashes)} stored listing hashes")
    
    print(f"[DEBUG] Initializing CraigslistScraper for job {job.id}")
    with CraigslistScraper.create(config) as scraper:
        upsert_listings = []
        listing_hashes = []
        print(f"[DEBUG] Starting scraping loop for job {job.id}")
        
        async for scrape_output in scraper.scrape():
            if isinstance(scrape_output, str):  # It's a hash
                listing_hashes.append(scrape_output)
            else:  # It's a new listing
                if isinstance(scrape_output, Listing) and scrape_output.hash not in stored_hashes:
                    upsert_listings.append(scrape_output)
                    stored_hashes.add(scrape_output.hash)
                
            if len(upsert_listings) >= BATCH_SIZE:
                upsert_listings = await batch_database_save(upsert_listings, job.id)
                    
        if upsert_listings:
            upsert_listings = await batch_database_save(upsert_listings, job.id)
            
        if listing_hashes:
            await batch_memoized_score_update(job.id, listing_hashes)

async def evaluate_job_listings(job: Job):
    """Evaluate listings for a specific job using its template criteria."""
    listing_scores = await get_job_listing_scores(job.id)
    
    print(f"\033[33mEvaluating listings for job: {job.name}")
    print(f"Found {len(listing_scores)} listings to evaluate\033[0m")
    
    for score in listing_scores:
        if score.score == 0:
            try:
                listing = await get_listing_by_id(score.listing_id)
                if not listing:
                    continue

                hueristic_score, hueristic_trace = evaluate_listing_hueristics(listing)
                aesthetic_score, aesthetic_trace = evaluate_listing_aesthetics(listing)
                total_score = hueristic_score + aesthetic_score
                total_trace = f"{hueristic_trace} | {aesthetic_trace}"
                
                await update_job_listing_score(job.id, listing.id, total_score, total_trace)
                
            except Exception as e:
                print(f"Error evaluating listing {score.listing_id}: {str(e)}")
                continue

@celery.task(bind=True, max_retries=1)
def run_single_job(self, job_id: UUID):
    """Run a complete job cycle - scraping and evaluation."""
    import asyncio
    
    async def _run_job():
        async with get_async_db() as session:
            job = await session.get(Job, job_id)
            if not job:
                raise ValueError(f"Job {job_id} not found")
            print(f"Running scrape listings for job {job_id}")
            await scrape_listings(job)
            print(f"Running evaluate job listings for job {job_id}")
            await evaluate_job_listings(job)
    
    asyncio.run(_run_job())

async def test_just_evaluation(job_id: UUID):
    async with get_async_db() as session:
        job = await session.get(Job, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        await evaluate_job_listings(job)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_job(UUID('031cbf19-3254-46e0-9d61-9b37e14255a5')))