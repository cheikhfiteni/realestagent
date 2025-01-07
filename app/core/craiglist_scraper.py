from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import json

import re
import asyncio
from typing import AsyncGenerator, Optional
from app.models.models import Listing
from app.core.base_scraper import BaseScraper, ScrapingConfig
from app.db.database import _listing_hash

class CraigslistScraper(BaseScraper):
    def __init__(self, config: ScrapingConfig):
        super().__init__(config)
        self.base_url = "https://craigslist.org/search/apa"
        self.sleep_time = 0.2

    def get_search_url(self) -> str:
        params = []
        if self.config.min_bedrooms:
            params.append(f"min_bedrooms={self.config.min_bedrooms}")
        if self.config.min_price:
            params.append(f"min_price={self.config.min_price}")
        if self.config.max_price:
            params.append(f"max_price={self.config.max_price}")
        
        query_string = "&".join(params)
        return f"{self.base_url}?{query_string}"

    async def get_listing_urls(self) -> AsyncGenerator[str, None]:
        page = 0
        visited_urls = set()
        
        while True:
            current_url = re.sub(r'gallery~\d+~0', f'gallery~{page}~0', self.get_search_url())
            self.driver.get(current_url)
            await asyncio.sleep(self.sleep_time)
            
            if self.driver.current_url in visited_urls:
                break
                
            visited_urls.add(self.driver.current_url)
            
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".gallery-card"))
                )
                
                links = [
                    element.find_element(By.CSS_SELECTOR, "a").get_attribute("href") 
                    for element in self.driver.find_elements(By.CSS_SELECTOR, ".gallery-card")
                ]
                
                for link in links:
                    yield link
                    
                page += 1
                await asyncio.sleep(self.sleep_time)
                
            except TimeoutException:
                break

    @staticmethod
    def _extract_housing_details(driver):
        try:
            attrs_element = driver.find_element(By.CLASS_NAME, "mapAndAttrs")
            attr_groups = attrs_element.find_elements(By.CLASS_NAME, "attrgroup")
            
            bedrooms = 0
            bathrooms = 0 
            square_footage = 0
            
            for group in attr_groups:
                spans = group.find_elements(By.TAG_NAME, "span")
                for span in spans:
                    text = span.text.lower()
                    if "br" in text:
                        try:
                            bedrooms = int(text.split("br")[0])
                        except ValueError:
                            pass
                    elif "ba" in text:
                        try:
                            bathrooms = float(text.split("ba")[0])
                        except ValueError:
                            pass
                    elif "ft" in text:
                        try:
                            square_footage = int(text.split("ft")[0])
                        except ValueError:
                            pass
            
            return bedrooms, bathrooms, square_footage
        except Exception:
            return 0, 0, 0
    
    @staticmethod
    def _extract_image_urls(driver) -> list[str]:
        """Extract image URLs from the listing page."""
        try:
            # Find the script tag containing image data under the multiimage div
            multiimage_div = driver.find_element(By.CLASS_NAME, "iw.multiimage")
            script_element = multiimage_div.find_element(By.TAG_NAME, "script")
            script_text = script_element.get_attribute("innerHTML")
            
            if "var imgList = " in script_text:
                # Extract the JSON array from the script
                json_str = script_text.split("var imgList = ")[1].strip().rstrip(";")
                img_list = json.loads(json_str)
                
                # Get the high quality image URLs
                return [img["url"].replace("600x450", "1200x900") for img in img_list]
            return []
        except Exception as e:
            print(f"Error extracting images: {str(e)}")
            return []

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
        if self.config.min_bedrooms and listing.bedrooms < self.config.min_bedrooms:
            return False
        if self.config.min_bathrooms and listing.bathrooms < self.config.min_bathrooms:
            return False
        if self.config.min_square_feet and listing.square_footage < self.config.min_square_feet:
            return False
        return True

    async def scrape(self) -> AsyncGenerator[Listing, None]:
        """Main scraping method that yields valid listings."""
        try:
            self.logger.info("Starting scraping process")
            async for url in self.get_listing_urls():
                self.logger.info(f"Scraping listing from URL: {url}")
                listing = await self.scrape_listing(url)
                if listing:
                    self.logger.info(f"Successfully scraped listing: {listing.title}")
                    if self.validate_listing(listing):
                        self.logger.info(f"Listing passed validation: {listing.title}")
                        # Create the listing object without any database operations
                        yield listing
                    else:
                        self.logger.info(f"Listing failed validation: {listing.title}")
                else:
                    self.logger.warning(f"Failed to scrape listing from URL: {url}")
        except Exception as e:
            self.logger.error(f"Error in scrape method: {str(e)}")
            raise