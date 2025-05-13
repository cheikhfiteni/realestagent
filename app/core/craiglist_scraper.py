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

# Regex to allow only alphanumeric characters for Craigslist location subdomains
VALID_LOCATION_REGEX = re.compile(r"^[a-zA-Z0-9]+$")

class CraigslistScraper(BaseScraper):
    def __init__(self, config: ScrapingConfig):
        super().__init__(config)
        self.base_url = "https://craigslist.org/search/apa"
        self.sleep_time = 0.2
        self.existing_hashes = set()
        self.max_listings_to_scrape = config.max_listings_to_scrape  # Store the limit

    def __enter__(self):
        print(f"[DEBUG] Entering CraigslistScraper context manager for job {self.config.template_id}")
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        print(f"[DEBUG] Exiting CraigslistScraper context manager for job {self.config.template_id}")

    def get_search_url(self) -> str:
        # Build base URL with location if provided
        base = "https://"
        if self.config.location:
            # Sanitize location to prevent redirection to arbitrary domains
            clean_location = self.config.location.lower().strip()
            if not VALID_LOCATION_REGEX.match(clean_location):
                raise ValueError(f"Invalid location format: '{self.config.location}'. Only alphanumeric characters are allowed.")
            else:
                base += f"{clean_location}."
        
        base += "craigslist.org/search/apa"

        # Build query parameters
        params = []
        if self.config.min_bathrooms:
            params.append(f"min_bathrooms={int(self.config.min_bathrooms)}")
        if self.config.min_bedrooms:
            params.append(f"min_bedrooms={int(self.config.min_bedrooms)}")
        if self.config.min_price:
            params.append(f"min_price={int(self.config.min_price)}")
        if self.config.max_price:
            params.append(f"max_price={self.config.max_price}")
        if self.config.zipcode and (clean_zipcode := re.sub(r"[^0-9]", "", str(self.config.zipcode))):
            params.append(f"postal={clean_zipcode}")
        if self.config.search_radius_miles and (clean_search_radius := re.sub(r"[^0-9]", "", str(self.config.search_radius_miles))):
            params.append(f"search_distance={clean_search_radius}")

        # Combine URL parts
        query_string = "&".join(params)
        url = f"{base}?{query_string}"

        print(f"[DEBUG] Constructed search URL: {url}")
        return url

    async def get_listing_urls(self) -> List[str]:
        page = 0
        visited_urls = set()
        all_links = []
        
        while True:
            current_url = f"{self.get_search_url()}#search=1~gallery~{page}~0"
            print(f"[DEBUG] Navigating to page {page} at URL: {current_url}")
            self.driver.get(current_url)
            await asyncio.sleep(self.sleep_time)
            
            if self.driver.current_url in visited_urls:
                print(f"[DEBUG] Already visited URL {self.driver.current_url}, breaking loop")
                break
                
            visited_urls.add(self.driver.current_url)
            print(f"[DEBUG] Added {self.driver.current_url} to visited URLs")
            
            try:
                print("[DEBUG] Waiting for gallery cards to load...")
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".gallery-card"))
                )
                
                links = [
                    element.find_element(By.CSS_SELECTOR, "a").get_attribute("href") 
                    for element in self.driver.find_elements(By.CSS_SELECTOR, ".gallery-card")
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
            # Look for housing info in multiple possible locations
            for selector in [
                ".attrgroup span",  # Primary housing details
                ".housing",  # Alternate location
                "[data-housing]"  # Data attribute fallback
            ]:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.lower()
                    
                    # Extract bedrooms
                    br_match = re.search(r'(\d+)\s*br', text)
                    if br_match and not bedrooms:
                        bedrooms = int(br_match.group(1))
                    
                    # Extract bathrooms
                    ba_match = re.search(r'(\d+(?:\.\d+)?)\s*ba', text)
                    if ba_match and not bathrooms:
                        bathrooms = float(ba_match.group(1))
                    
                    # Extract square footage - now handling decimals
                    sqft_match = re.search(r'(\d+(?:\.\d+)?)\s*ft', text)
                    if sqft_match and not square_footage:
                        # Round to nearest integer
                        square_footage = round(float(sqft_match.group(1)))
                
                # If we found all details, break early
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
            # Try multiple selectors for different image scenarios
            for selector in [
                ".iw.multiimage",  # Multiple images case
                "#thumbs",         # Single image case
                ".gallery"         # Alternative gallery class
            ]:
                try:
                    container = driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # For multiple images case
                    script_elements = container.find_elements(By.TAG_NAME, "script")
                    for script in script_elements:
                        script_text = script.get_attribute("innerHTML")
                        if "var imgList = " in script_text:
                            json_str = script_text.split("var imgList = ")[1].strip().rstrip(";")
                            img_list = json.loads(json_str)
                            return [img["url"].replace("600x450", "1200x900") for img in img_list]
                    
                    # For single image case
                    img_elements = container.find_elements(By.TAG_NAME, "img")
                    if img_elements:
                        for img in img_elements:
                            src = img.get_attribute("src")
                            if src:
                                # Convert to high quality if possible
                                image_urls.append(src.replace("600x450", "1200x900"))
                        if image_urls:
                            return image_urls
                
                except Exception:
                    continue
            
            return image_urls  
            
        except Exception as e:
            print(f"Error extracting images: {str(e)}")
            return []  # Return empty list on any error

    @staticmethod
    def _normalize_description(html_content: str) -> str:
        """Convert HTML description to clean text with normalized newlines."""
        # Remove any special divs like print-information
        html_content = re.sub(r'<div class="print-information.*?</div>', '', html_content, flags=re.DOTALL)
        # Replace <br> and <br/> tags with newlines
        text = re.sub(r'<br\s*/?>|</div>|</p>', '\n', html_content)
        # Remove any remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Clean up extra whitespace and newlines
        text = re.sub(r'\n\s*\n', '\n\n', text.strip())
        return text

    async def scrape_listing(self, url: str) -> Optional[Listing]:
        """Extract listing information from a Craigslist posting."""
        try:
            self.driver.get(url)
            
            # Wait for title element to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "postingtitletext"))
            )
            
            title_element = self.driver.find_element(By.ID, "titletextonly")
            title = title_element.text if title_element else ""

            post_id = url.split("/")[-1].split(".")[0]
            
            price_element = self.driver.find_element(By.CLASS_NAME, "price") 
            price = int(price_element.text.replace("$", "").replace(",", "")) if price_element else 0
            
            # More resilient location extraction
            try:
                location_element = self.driver.find_element(By.CLASS_NAME, "mapaddress")
                location = location_element.text if location_element else ""
            except:
                # Fallback location extraction
                try:
                    location_element = self.driver.find_element(By.CSS_SELECTOR, "[data-latitude]")
                    location = location_element.get_attribute("data-address") or ""
                except:
                    location = ""
            
            neighborhood_element = self.driver.find_element(By.XPATH, "//span[@class='postingtitletext']/span[3]")
            neighborhood = neighborhood_element.text.strip("()") if neighborhood_element else ""

            description_element = self.driver.find_element(By.ID, "postingbody")
            description = self._normalize_description(description_element.get_attribute('innerHTML')) if description_element else ""
                    
            bedrooms, bathrooms, square_footage = self._extract_housing_details(self.driver)
            image_urls = self._extract_image_urls(self.driver)

            await asyncio.sleep(self.sleep_time)  # Add small delay between requests

            return Listing(
                hash=_listing_hash(post_id),
                title=title,
                price=price,
                link=url,
                post_id=post_id,
                description=description,
                location=location,
                neighborhood=neighborhood,
                bedrooms=bedrooms, 
                bathrooms=bathrooms,
                square_footage=square_footage,
                image_urls=json.dumps(image_urls)
            )
            
        except Exception as e:
            self.logger.error(f"Error scraping listing: {str(e)}")
            return None

    def validate_listing(self, listing: Listing) -> bool:
        """Validate listing meets minimum criteria"""
        print(f"[DEBUG] Validating listing: {listing.title}, {listing.price}, {listing.bedrooms}, {listing.bathrooms}, {listing.square_footage}")
        if self.config.min_bedrooms and listing.bedrooms < self.config.min_bedrooms:
            return False
        if self.config.min_bathrooms and listing.bathrooms < self.config.min_bathrooms:
            return False
        if self.config.min_square_feet and listing.square_footage < self.config.min_square_feet:
            return False
        return True

    async def load_existing_hashes(self):
        """Load existing listing hashes from database"""
        self.existing_hashes = get_stored_listing_hashes()
        print(f"[DEBUG] Loaded {len(self.existing_hashes)} existing listing hashes")

    async def scrape(self) -> AsyncGenerator[ScrapeOutput, None]:
        """Main scraping method that yields either new listings or existing listing hashes."""
        print(f"[DEBUG] In the craiglist scraping loop for the task {self.config.template_id}")
        scraped_count = 0 # Counter for scraped items
        try:
            self.logger.info(f"Starting scraping process. Limit: {self.max_listings_to_scrape}")
            # Load existing hashes before starting
            await self.load_existing_hashes()
            urls = await self.get_listing_urls()
            print(f"[DEBUG] Found {len(urls)} potential listings")
            for url in urls:
                # Check scrape limit
                if self.max_listings_to_scrape is not None and scraped_count >= self.max_listings_to_scrape:
                    self.logger.info(f"Reached scrape limit of {self.max_listings_to_scrape}. Stopping.")
                    break 
                
                # Check if listing already exists before scraping
                post_id = url.split("/")[-1].split(".")[0]
                listing_hash = _listing_hash(post_id)
                
                if listing_hash in self.existing_hashes:
                    self.logger.info(f"Found existing listing (hash): {url}")
                    yield listing_hash
                    continue

                # Only add to existing_hashes if it's truly new to avoid double counting later
                # self.existing_hashes.add(listing_hash) # Moved inside the 'if listing' block
                self.logger.info(f"Scraping new listing from URL: {url}")
                listing = await self.scrape_listing(url)
                
                if listing:
                    self.existing_hashes.add(listing.hash) # Add hash after confirming scrape
                    self.logger.info(f"Successfully scraped listing: {listing.title}")
                    if self.validate_listing(listing):
                        self.logger.info(f"Listing passed validation: {listing.title}")
                        yield listing
                        scraped_count += 1 # Increment count only for yielded new listings
                    else:
                        self.logger.info(f"Listing failed validation: {listing.title}")
                else:
                    self.logger.warning(f"Failed to scrape listing from URL: {url}")
        except Exception as e:
            self.logger.error(f"Error in scrape method: {str(e)}")
            raise