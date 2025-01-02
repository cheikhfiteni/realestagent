from abc import ABC, abstractmethod
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from contextlib import contextmanager

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

class BaseScraper(ABC):
    def __init__(self):
        self._driver_manager = DriverManager.get_instance()

    @property
    def driver(self):
        return self._driver_manager.get_driver()

    @abstractmethod
    def scrape_listing(self, url: str):
        pass

    @classmethod
    @contextmanager
    def create(cls):
        scraper = cls()
        try:
            yield scraper
        finally:
            # use this to clean up scrapers but notquit the driver
            pass 