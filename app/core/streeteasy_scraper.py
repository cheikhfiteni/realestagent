

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import json

import re
import asyncio
from typing import AsyncGenerator, List, Optional
from app.models.models import Listing
from app.core.base_scraper import BaseScraper, ScrapingConfig, ScrapeOutput
from app.db.database import _listing_hash, get_stored_listing_hashes

class StreeteasyScraper(BaseScraper):
    def __init__(self, config: ScrapingConfig):
        super().__init__(config)
        self.base_url = "https://streeteasy.com/for-rent/"
        self.sleep_time = 0.2
        self.existing_hashed = set()
    
    def __enter__(self):
        print(f"[DEBUG] Entering CraigslistScraper context manager for job {self.config.job_id}")
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        print(f"[DEBUG] Exiting CraigslistScraper context manager for job {self.config.job_id}")
    
    def get_search_url(self) -> str:
        base = self.base_url

        if self.config.location:
            location = self.config.location.replace(" ", "-")
            base += location 

        parems = []
        sortby = []
        if self.config.min_price and self.config.max_price:
            parems.append(f"price:{int(self.config.min_price)}-{int(self.config.max_price)}")
        elif self.config.min_price:
            parems.append(f"price:{int(self.config.min_price)}-")  
        elif self.config.max_price:
            parems.append(f"price:-{int(self.config.max_price)}")
        if self.config.min_square_feet:
            parems.append(f"sqft>={self.config.min_square_feet}")
        if self.config.zipcode:
            parems.append(f"zip:{self.config.zipcode}")
        if self.config.min_bedrooms:
            parems.append(f"beds:{int(self.config.min_bedrooms)}")
        # TODO: streeteasy bedroom selector diff have to add max_bedrooms to base_scraper
        if self.config.min_bathrooms:
            parems.append(f"baths>={int(self.config.min_bathrooms)}")


        sortby.append(f"sort_by=se_score")

        query_string = "%7C".join(parems)
        url = f"{base}/{query_string}?{sortby}"

        print(f"[DEBUG] Generated search URL: {url}")
        return url

    async def get_listing_urls(self) -> List[str]:
        page = 1
        visited_urls = set()
        all_links = []

        while True:
            current_url = f"{self.get_search_url()}&page={page}"
            print(f"[DEBUG] Navigating to page {page} at URL: {current_url}")
            self.driver.get(current_url)
            await asyncio.sleep(self.sleep_time)

            if self.driver.current_url in visited_urls:
                print("[DEBUG] Already visited URL {self.driver.current_url}, breaking loop")
                break
            
            visited_urls.add(self.driver.current_url)
            print(f"[DEBUG] Added {self.driver.current_url} to visited URLs")

            try:
                print("[DEBUG] Waiting for gallery cards to load...")
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='listing-card']"))
                )
                links = [
                    element.find_element(By.CSS_SELECTOR, "a").get_attribute("href") 
                    for element in self.driver.find_elements(By.CSS_SELECTOR, "[data-testid='listing-card']")

                ]
                print(f"[DEBUG] Found {len(links)} listing links on page {page}")
                
                all_links.extend(links)
                    
                page += 1
                print(f"[DEBUG] Moving to page {page}")
                await asyncio.sleep(self.sleep_time)
                
            except TimeoutException:
                print("[DEBUG] Timeout waiting for gallery cards, breaking loop")
                break
        print(f"[DEBUG] Total links found: {len(all_links)}")
        return all_links