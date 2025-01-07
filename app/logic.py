from app.core.evaluator import evaluate_listing_aesthetics, evaluate_listing_hueristics
from app.models.models import Listing, Job
from app.config import CRAIGSLIST_URLS
from app.db.database import (
    get_async_db, get_stored_listing_hashes, save_new_listings_to_db,
    update_job_listing_score
)

from app.core.base_scraper import ScrapingConfig
from app.core.craiglist_scraper import CraigslistScraper

BATCH_SIZE = 5
SLEEP_TIME = 0.2

async def scrape_listings(job: Job):
    config = ScrapingConfig.from_job_template(job.template)
    
    with CraigslistScraper.create(config) as scraper:
        upsert_listings = []
        stored_hashes = get_stored_listing_hashes()
        
        for listing in scraper.scrape():
            if listing.hash not in stored_hashes:
                upsert_listings.append(listing)
                
                if len(upsert_listings) >= BATCH_SIZE:
                    save_new_listings_to_db(upsert_listings)
                    for listing in upsert_listings:
                        await update_job_listing_score(job.id, listing.id, 0, "")
                    stored_hashes.update([l.hash for l in upsert_listings])
                    upsert_listings = []
                    
        if upsert_listings:
            save_new_listings_to_db(upsert_listings)
            stored_hashes.update([l.hash for l in upsert_listings])

async def evaluate_job_listings(job: Job):
    """Evaluate listings for a specific job using its template criteria."""
    listing_scores = job.listing_scores or {}
    
    for listing_id, score_data in listing_scores.items():
        if score_data.get("score", 0) == 0:  # Only evaluate unevaluated listings
            try:
                hueristic_score, hueristic_trace = evaluate_listing_hueristics(listing_id)
                aesthetic_score, aesthetic_trace = evaluate_listing_aesthetics(listing_id)
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
            
        # Run scraper for each URL
        for base_url in CRAIGSLIST_URLS:
            await scrape_listings(base_url, job)
            
        # Evaluate all listings
        await evaluate_job_listings(job)

if __name__ == "__main__":
    import asyncio
    asyncio.run(run_job(1))  # For testing