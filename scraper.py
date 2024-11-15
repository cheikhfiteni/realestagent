from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import re
import json
from models import Listing
from database import _listing_hash

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
    
def _extract_image_urls(driver: webdriver.Chrome) -> list[str]:
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

def _get_information_from_listing(url: str, driver: webdriver.Chrome):
    driver.get(url)
    
    try:
        # Wait for title element to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "postingtitletext"))
        )
        
        title_element = driver.find_element(By.ID, "titletextonly")
        title = title_element.text if title_element else ""

        post_id = url.split("/")[-1].split(".")[0]
        
        price_element = driver.find_element(By.CLASS_NAME, "price") 
        price = int(price_element.text.replace("$", "").replace(",", "")) if price_element else 0
        
        location_element = driver.find_element(By.CLASS_NAME, "mapaddress")
        location = location_element.text if location_element else ""
        
        neighborhood_element = driver.find_element(By.XPATH, "//span[@class='postingtitletext']/span[3]")
        neighborhood = neighborhood_element.text.strip("()") if neighborhood_element else ""

        description_element = driver.find_element(By.ID, "postingbody")
        description = _normalize_description(description_element.get_attribute('innerHTML')) if description_element else ""
                
        bedrooms, bathrooms, square_footage = _extract_housing_details(driver)
        image_urls = _extract_image_urls(driver)

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
        print(f"Error extracting listing data: {str(e)}")
        return None
