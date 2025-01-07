from abc import ABC, abstractmethod
from typing import Generator, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from contextlib import contextmanager
from app.models.models import Listing, JobTemplate
import logging
import os

class DriverManager:
    _instance = None
    _driver = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_driver(self):
        if self._driver is None:
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.binary_location = "/usr/bin/chromium"
            chrome_options.add_argument('--disable-gpu')
            
            if os.environ.get("DEBUG"):
                chrome_options.add_argument('--enable-logging')
                chrome_options.add_argument('--v=1')
                chrome_options.add_argument('--remote-debugging-port=9222')
                chrome_options.add_argument('--remote-debugging-address=0.0.0.0')
                chrome_options.add_argument('--enable-crash-reporter')

            self._driver = webdriver.Remote(
                command_executor='http://selenium:4444/wd/hub',
                options=chrome_options
            )     
        return self._driver

    def quit_driver(self):
        if self._driver:
            self._driver.quit()
            self._driver = None

class ScrapingConfig:
    """Configuration class for scraper parameters"""
    def __init__(
        self,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_bedrooms: Optional[int] = None,
        min_bathrooms: Optional[float] = None,
        min_square_feet: Optional[int] = None,
        location: Optional[str] = None,
        max_listings: int = 100,
        search_radius_miles: float = 10.0
    ):
        self.min_price = min_price
        self.max_price = max_price
        self.min_bedrooms = min_bedrooms
        self.min_bathrooms = min_bathrooms
        self.min_square_feet = min_square_feet
        self.location = location
        self.max_listings = max_listings
        self.search_radius_miles = search_radius_miles

    @classmethod
    def from_job_template(cls, template: JobTemplate) -> 'ScrapingConfig':
        """Create config from a job template"""
        return cls(
            min_bedrooms=template.min_bedrooms,
            min_bathrooms=template.min_bathrooms,
            min_square_feet=template.min_square_feet,
        )

class BaseScraper(ABC):
    def __init__(self, config: ScrapingConfig):
        self._driver_manager = DriverManager.get_instance()
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    def driver(self):
        return self._driver_manager.get_driver()

    @abstractmethod
    def get_search_url(self) -> str:
        """Generate the initial search URL based on config"""
        pass

    @abstractmethod
    def get_listing_urls(self, base_search_url: str) -> Generator[str, None, None]:
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

    def scrape(self) -> Generator[Listing, None, None]:
        """Main scraping workflow"""
        try:
            search_url = self.get_search_url()
            self.driver.get(search_url)
            
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