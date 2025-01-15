from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import json
import urllib.parse

import uuid
import re
import asyncio
from typing import AsyncGenerator, List, Optional
from app.models.models import Listing
from app.core.base_scraper import BaseScraper, ScrapingConfig, ScrapeOutput
from app.db.database import _listing_hash, get_stored_listing_hashes



class ZillowScraper(BaseScraper):
    def __init__(self, config: ScrapingConfig):
        super().__init__(config)
        self.base_url = "https://www.zillow.com/"
        self.sleep_time = 0.2
        self.existing_hashes = set()
    
    def __enter__(self):
        print(f"[DEBUG] Entering ZillowScraper context manager for job {self.config.job_id}")
        return self
    def __exit__(self, exc_type, exc_value, trackeback):
        print(f"[DEBUG] Exiting ZillowScraper context manager for job {self.config.job_id}")

    # structure of zillow url for rentals is zillow.com/location/rentals
    def get_search_url(self, page: int = 1) -> str:
        base = self.base_url

        # TODO: consider if user inputed full state name instead of shorthand
        if self.config.location:
            # zillow url replaces spaces with dashes 
            location = self.config.location.replace(" ", "-").lower()
            base += f"{location}/rentals/"

        # URL with paramters/filters is encoded so have to build searchQueryState
        search_query_state = {
        "pagination": {"currentPage": page},  
        "isMapVisible": True,  
        "filterState": {
            "sort": {"value": "priorityscore"},
            "fr": {"value": True},
            "fsba": {"value": False},  # for sale by agent
            "fsbo": {"value": False}, #for sale by owner - both to false priortizing for rent
            "nc": {"value": False},   # new constuction
            "cmsn": {"value": False}, # coming soon
            "auc": {"value": False}, # auction
            "fore": {"value": False}, #foreclosure
            "mf": {"value": False},       # multi family homes
            "land":{"value": False},     # land
            "manu": {"value": False},   # manufactured homes
            "mp": {"max": self.config.max_price if self.config.max_price else None, "min": self.config.min_price if self.config.min_price else None},
            "baths": {"min": self.config.min_bathrooms if self.config.min_bathrooms else None},
            "sqft": {"min": self.config.min_square_feet if self.config.min_square_feet else None},
            "beds": {"min": self.config.min_bedrooms if self.config.min_befrooms else None},
        },  
        "isListVisible": True,
        "mapZoom": 12, # hard coded a random number but def not good practice TODO: CHANGE
        "usersSearchTerm": self.config.location.replace(" ", ""),  
        # TODO: if person inputed California instead of CA this wont work figure that out
        }

         # Remove None values for cleaner URLs - gpt recommendation
        search_query_state["filterState"] = {k: v for k, v in search_query_state["filterState"].items() if v["value"] is not None}

        encoded_state = urllib.parse.quote(json.dumps(search_query_state))

        full_url = f"{base}?searchQueryState={encoded_state}"
        print(f"[DEBUG] Constructed Zillow search URL: {full_url}")
        return full_url
    
    async def get_listing_urls(self) -> List[str]:
       curr_page = 1
       visited_urls = set()
       all_links = []

       while True:
           current_url = self.get_search_url(self, curr_page)
           print(f"[DEBUG] Navigating to page {curr_page}")
           self.driver.get(current_url)
           await asyncio.sleep(self.sleep_time)

           if self.driver.current_url in visited_urls:
               print(f"[DEBUG] Already visited url {self.driver.current_url}, breaking loop")
               break
           visited_urls.add(self.driver.current_url)
           print(f"[DEBUG] Added {self.driver.current_url} to visited URLs")

           try:
                print("[DEBUG] Waiting for gallery cards to load...")
                WebDriverWait(self.driver, 10).until(
                    # Not sure if this is right css selector zillow source code so hard to go through
                    # Alternative to css selectors is property date in source code but code for that complicated for me
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".ListItem-c11n-8-107-0__sc-13rwu5a-0 StyledListCardWr apper-srp-8-107-0_ sc-wtsrtn-0 dAZKuw XoFGK"))
                )
        
        # TODO: BIGGEST PROBLEMS: zillow links to each listing not in page source 