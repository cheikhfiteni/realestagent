from app.core.evaluator import evaluate_listing_aesthetics, evaluate_listing_hueristics
from app.models.models import Listing, Job
from app.db.database import (
    get_async_db, get_stored_listing_hashes, save_new_listings_to_db,
    update_job_listing_score, get_listing_by_id
)

from app.core.base_scraper import ScrapingConfig
from app.core.craiglist_scraper import CraigslistScraper

BATCH_SIZE = 5
SLEEP_TIME = 0.2

async def batch_database_save(upsert_listings, job_id):
    save_new_listings_to_db(upsert_listings)
    for listing in upsert_listings:
        await update_job_listing_score(job_id, listing.id, 0, "")
    return []

async def scrape_listings(job: Job):
    config = ScrapingConfig.from_job_template(job.template)
    stored_hashes = get_stored_listing_hashes()
    
    with CraigslistScraper.create(config) as scraper:
        upsert_listings = []
        
        async for listing in scraper.scrape():
            if listing.hash not in stored_hashes:
                upsert_listings.append(listing)
                stored_hashes.add(listing.hash)
                
            if len(upsert_listings) >= BATCH_SIZE:
                upsert_listings = await batch_database_save(upsert_listings, job.id)
                    
        if upsert_listings:
            upsert_listings = await batch_database_save(upsert_listings, job.id)

async def evaluate_job_listings(job: Job):
    """Evaluate listings for a specific job using its template criteria."""
    listing_scores = job.listing_scores or {}
    
    for listing_id, score_data in listing_scores.items():
        if score_data.get("score", 0) == 0:
            try:
                listing = await get_listing_by_id(listing_id)
                if not listing:
                    continue

                hueristic_score, hueristic_trace = evaluate_listing_hueristics(listing)
                aesthetic_score, aesthetic_trace = evaluate_listing_aesthetics(listing)
                total_score = hueristic_score + aesthetic_score
                total_trace = f"{hueristic_trace} | {aesthetic_trace}"
                
                await update_job_listing_score(job.id, int(listing_id), total_score, total_trace)
                
            except Exception as e:
                print(f"Error evaluating listing {listing_id}: {str(e)}")
                continue

async def run_job(job_id: int):
    """Run a complete job cycle - scraping and evaluation."""
    async with get_async_db() as session:
        job = await session.get(Job, job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        print(f"Running scrape listings for job {job_id}")
        await scrape_listings(job)
        print(f"Running evaluate job listings for job {job_id}")
        await evaluate_job_listings(job)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_job(1))  # For testing