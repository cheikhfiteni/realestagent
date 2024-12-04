from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import time
import re
from app.core.evaluator import evaluate_unevaluated_listings
from app.models.models import Listing
from app.config import CRAIGSLIST_URLS
from app.db.database import get_stored_listing_hashes, save_new_listings_to_db, _listing_hash
from app.core.scraper import _get_information_from_listing

BATCH_SIZE = 5
SLEEP_TIME = 0.2

def scrape_listings(base_url: str):
    driver = webdriver.Chrome()
    stored_hashes = get_stored_listing_hashes()

    visited_urls = set()
    page = 0

    upsert_listings = []
    
    while True:
        # uses craiglist redirect to check if end of gallery
        current_url = re.sub(r'gallery~\d+~0', f'gallery~{page}~0', base_url)
        driver.get(current_url)
        time.sleep(SLEEP_TIME*25)
        final_url = driver.current_url
        
        if final_url in visited_urls:
            print("Results are ready - reached previously visited page")
            break

        visited_urls.add(final_url) 
        
        try:
            # Wait for listings to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".gallery-card"))
            )
            
            links = [element.find_element(By.CSS_SELECTOR, "a").get_attribute("href") 
                     for element in driver.find_elements(By.CSS_SELECTOR, ".gallery-card")]
            
            for link in links:
                try:
                    post_id = link.split("/")[-1].split(".")[0]
                
                    if _listing_hash(post_id) in stored_hashes:
                        continue
                    
                    listing_data: Listing = _get_information_from_listing(link, driver)
                    upsert_listings.append(listing_data)

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
            time.sleep(SLEEP_TIME)  # Be nice to Craigslist
            
        except TimeoutException:
            print("Results are ready - no more listings found")
            break

    if upsert_listings:
        print(f"Saving remaining {len(upsert_listings)} listings to database")
        save_new_listings_to_db(upsert_listings)
        stored_hashes.update([listing.hash for listing in upsert_listings])
                
    driver.quit()

if __name__ == "__main__":
    for base_url in CRAIGSLIST_URLS:
        scrape_listings(base_url)
    evaluate_unevaluated_listings()