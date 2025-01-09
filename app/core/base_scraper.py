from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from contextlib import contextmanager
import time

from uuid import UUID
from app.models.models import Listing, JobTemplate
from app.config import SELENIUM_HOST
import logging

class DriverManager:
    _instance = None
    _driver = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_driver(self):
        max_retries = 3
        retry_delay = 2  # seconds
        timeout = 10  # seconds
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # check if the driver is expired
                if self._driver:
                    try:
                        self._driver.current_url
                        return self._driver
                    except Exception:
                        self.logger.info("Selenium session expired, recreating driver")
                        self.quit_driver()
                
                # Create new driver if none exists or previous one failed
                chrome_options = Options()
                chrome_options.add_argument('--headless=new')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--disable-gpu')
                
                chrome_options.add_argument('--enable-logging')
                chrome_options.add_argument('--v=1')

                selenium_url = f'{SELENIUM_HOST}:4444/wd/hub'
                print(f"\033[35mConnecting to Selenium at: {selenium_url}\033[0m")

                self._driver = webdriver.Remote(
                    command_executor=selenium_url,
                    options=chrome_options
                )     
                return self._driver

            except Exception as e:
                print(f"Failed to create driver (attempt {max_retries}): {e}")
                self.quit_driver()  # Cleanup on failure
                if time.time() - start_time >= timeout:
                    raise TimeoutError(f"Failed to connect to Selenium after {timeout} seconds")
                time.sleep(retry_delay)
                continue

        raise TimeoutError(f"Failed to connect to Selenium after {timeout} seconds")

    def quit_driver(self):
        if self._driver:
            self._driver.quit()
            self._driver = None

    def __del__(self):
        self.quit_driver()

class ScrapingConfig:
    """Configuration class for scraper parameters"""
    def __init__(
        self,
        template_id: UUID,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_bedrooms: Optional[int] = None,
        min_bathrooms: Optional[float] = None,
        min_square_feet: Optional[int] = None,
        location: Optional[str] = None,
        zipcode: Optional[str] = None,
        search_radius_miles: float = 10.0
    ):
        self.template_id = template_id
        self.min_price = min_price
        self.max_price = max_price
        self.min_bedrooms = min_bedrooms
        self.min_bathrooms = min_bathrooms
        self.min_square_feet = min_square_feet
        self.location = location
        self.zipcode = zipcode
        self.search_radius_miles = search_radius_miles
    @classmethod
    def from_job_template(cls, template: JobTemplate) -> 'ScrapingConfig':
        """Create config from a job template"""
        return cls(
            template_id=template.id,
            min_bedrooms=template.min_bedrooms,
            min_bathrooms=template.min_bathrooms,
            min_square_feet=template.min_square_feet,
            location=template.location,
            zipcode=template.zipcode,
            search_radius_miles=template.search_distance_miles
        )

class BaseScraper(ABC):
    def __init__(self, config: ScrapingConfig):
        self._driver_manager = DriverManager.get_instance()
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        self.logger.setLevel(logging.INFO)

    @property
    def driver(self):
        return self._driver_manager.get_driver()

    @abstractmethod
    def get_search_url(self) -> str:
        """Generate the initial search URL based on config"""
        pass

    @abstractmethod
    def get_listing_urls(self, base_search_url: str) -> List[str]:
        """Extract listing URLs from search results pages"""
        pass

    @abstractmethod
    def scrape_listing(self, url: str) -> Optional[Listing]:
        """Scrape a single listing page and return structured data"""
        pass

    @abstractmethod
    def validate_listing(self, listing: Listing) -> bool:
        """Validate if a listing meets the minimum criteria"""
        pass

    async def scrape(self) -> AsyncGenerator[Listing, None]:
        """Main scraping workflow"""
        try:
            search_url = self.get_search_url()
            try:
                self.driver.get(search_url)
            except (TimeoutException, WebDriverException) as e:
                self.logger.error(f"Failed to connect to Selenium or load page: {str(e)}")
                self._driver_manager.quit_driver()
                raise
            
            for listing_url in self.get_listing_urls(search_url):
                try:
                    listing = self.scrape_listing(listing_url)
                    if listing and self.validate_listing(listing):
                        yield listing
                except Exception as e:
                    self.logger.error(f"Error scraping listing {listing_url}: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error in scraping workflow: {str(e)}")
            raise

    @classmethod
    @contextmanager
    def create(cls, config: ScrapingConfig):
        scraper = cls(config)
        try:
            yield scraper
        finally:
            pass 