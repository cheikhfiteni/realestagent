

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

        # Search parameters
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

    @staticmethod
    def _extract_housing_details(driver):
        """Extract housing details with improved reliability."""
        bedrooms = bathrooms = square_footage = 0

        try:
            selectors = [".Body_base_gyzqw"]
            for selector in selectors:
                
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.lower()

                    # Bedrooms
                    br_match = re.search(r'(\d+)\s*bed', text)
                    if br_match and not bedrooms:
                        bedrooms = int(br_match.group(1))

                    # Bathrooms
                    ba_match = re.search(r'(\d+)\s*bath', text)
                    if ba_match and not bathrooms:
                        bathrooms = float(ba_match.group(1))

                    if "-" not in text:
                        sqft_match = re.search(r'(\d+(?:\.\d+)?)\s*ft²', text)
                        if sqft_match and not square_footage:
                            square_footage = round(float(sqft_match.group(1)))
                if bedrooms and bathrooms and square_footage:
                    break
                
        except Exception as e:
            print(f"Error extracting housing details: {str(e)}")

        return bedrooms, bathrooms, square_footage
        
    @staticmethod
    def _extract_image_urls(driver) -> list[str]:
        """Extract image URLs from the listing page."""
        image_urls = []

        try:
            selectors = [".MediaCarousel_mediaCarouselImageWrapper_p3Fsm",
                        ".MediaCarousel_thumbsContainer_A9ynS"
                        ]
            # ? I dont split into two cases of multi-image/single image dont see what I have to
            for selector in selectors:
                try:
                    # Locate the container for images
                    container = driver.find_element(By.CSS_SELECTOR, selector)

                    # Extract image URLs from <img> tags
                    img_elements = container.find_elements(By.XPATH, ".//img[starts-with(@alt, 'photo')]")
                    for img in img_elements:
                        src = img.get_attribute("src")
                        if src:
                            high_res_url = src.replace("800_400", "1200_800")  # Adjust resolution
                            image_urls.append(high_res_url)

                    # If images found, stop looking further
                    if image_urls:
                        return image_urls

                except Exception:
                    # Skip to next selector on failure
                    continue

            return image_urls
        
        except Exception as e:
            print(f"Error extracting images: {str(e)}")
            return []  # Return empty list on any error
    
    @staticmethod
    def _normalize_description(html_content: str) -> str:
        """Convert HTML description to clean text with normalized newlines."""
       # TODO: Figure out if how to remove any special divs 
        # Replace <br> and <br/> tags with newlines
        text = re.sub(r'<br\s*/?>|</div>|</p>', '\n', html_content)
        # Remove any remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Clean up extra whitespace and newlines
        text = re.sub(r'\n\s*\n', '\n\n', text.strip())
        return text
        
    async def scrape_listing(self, url: str) -> Optional[Listing]:
        try:
            self.driver.get(url)

            # Title, price, etc heading
            WebDriverWait(self.driver, 10).until(
                  EC.presence_of_all_elements_located(By.CSS_SELECTOR, "[data-testid='home-info-section']")
            )

            title_element = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='home-info-section']")
            title = title_element.text if title_element else ""

            post_id = url.split("/")[-1].split(".")[0]

            price_element = self.driver.find_element(By.CLASS_NAME, "SecondaryLarge_base_XChiP SecondaryLarge_fontWeightLight_AQq-k PriceInfo_price__HK81g")
            price = int(price_element.text.replace("$", "").replace(",", "")) if price_element else 0

            try:
                location_element = self.driver.find_element(By.CLASS_NAME, "Body_base_gyzqw AboutBuildingSection_address__TdYEX")
                location = location_element.text if location_element else ""

            except:
                # ? When tested latitude longitude location said bot detected?? so left out
                location = ""

            neighborhood_element = self.driver.find_element(B)