from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options

import time
import re
from app.core.evaluator import evaluate_listing_aesthetics, evaluate_listing_hueristics
from app.models.models import Listing, Job
from app.config import CRAIGSLIST_URLS
from app.db.database import (
    get_async_db, get_stored_listing_hashes, save_new_listings_to_db, _listing_hash,
    update_job_listing_score
)
from app.core.scraper import _get_information_from_listing

BATCH_SIZE = 5
SLEEP_TIME = 0.2

async def scrape_listings(base_url: str, job: Job):
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Add these Chromium-specific options
        chrome_options.binary_location = "/usr/bin/chromium"
        chrome_options.add_argument('--disable-gpu')
        
        # Remove or comment out these as they might not be needed/supported
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--v=1')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--remote-debugging-address=0.0.0.0')
        chrome_options.add_argument('--enable-crash-reporter')
        
        driver = webdriver.Remote(
            command_executor='http://selenium:4444/wd/hub',
            options=chrome_options
        )
        
        print("Chrome started successfully!")
        stored_hashes = get_stored_listing_hashes()

        visited_urls = set()
        page = 0

        upsert_listings = []
        
        while True:
            current_url = re.sub(r'gallery~\d+~0', f'gallery~{page}~0', base_url)
            driver.get(current_url)
            time.sleep(SLEEP_TIME*25)
            final_url = driver.current_url
            
            if final_url in visited_urls:
                print("Results are ready - reached previously visited page")
                break

            visited_urls.add(final_url) 
            
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".gallery-card"))
                )

                results_container = driver.find_element(By.CSS_SELECTOR, ".results.cl-results-page")
                print(results_container.get_attribute('outerHTML'))

                with open('page_structure.html', 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                            
                links = [element.find_element(By.CSS_SELECTOR, "a").get_attribute("href") 
                         for element in driver.find_elements(By.CSS_SELECTOR, ".gallery-card")]
                
                for link in links:
                    try:
                        post_id = link.split("/")[-1].split(".")[0]
                        listing_hash = _listing_hash(post_id)
                        
                        # Add to job's listing scores if new
                        if listing_hash not in stored_hashes:
                            listing_data: Listing = _get_information_from_listing(link, driver)
                            if listing_data:  # Check if listing data was successfully retrieved
                                upsert_listings.append(listing_data)
                                
                                # Save listings first
                                if len(upsert_listings) >= BATCH_SIZE:
                                    print(f"Saving {len(upsert_listings)} listings to database")
                                    save_new_listings_to_db(upsert_listings)
                                    
                                    # Now update scores for the saved listings
                                    for listing in upsert_listings:
                                        await update_job_listing_score(job.id, listing.id, 0, "")
                                        
                                    stored_hashes.update([listing.hash for listing in upsert_listings])
                                    upsert_listings = []
                                time.sleep(SLEEP_TIME)

                        if len(upsert_listings) >= BATCH_SIZE:
                            print(f"Saving {len(upsert_listings)} listings to database")
                            save_new_listings_to_db(upsert_listings)
                            stored_hashes.update([listing.hash for listing in upsert_listings])
                            upsert_listings = []
                        time.sleep(SLEEP_TIME)

                    except Exception as e:
                        print(f"Error processing listing: {str(e)}")
                        continue
                
                page += 1
                time.sleep(SLEEP_TIME)
                
            except TimeoutException:
                print("Results are ready - no more listings found")
                break

        if upsert_listings:
            print(f"Saving remaining {len(upsert_listings)} listings to database")
            save_new_listings_to_db(upsert_listings)
            stored_hashes.update([listing.hash for listing in upsert_listings])
                
        driver.quit()
    except (TimeoutException, WebDriverException) as e:
        print(f"Selenium error: {str(e)}")
        driver.quit()
        raise

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