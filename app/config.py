from pydantic import BaseModel
import os

CRAIGSLIST_URLS = [
    "https://sfbay.craigslist.org/search/apa?min_bathrooms=2&min_bedrooms=4&postal=94142&search_distance=1#search=1~gallery~0~0",
]


def normalize_db_url(url: str) -> str:
    """Ensure database URL uses postgresql:// instead of postgres:// and handles SSL parameters"""
    return url if not url else url.replace('postgres://', 'postgresql://', 1)

# Database settings
DATABASE_URL = normalize_db_url(os.getenv("DATABASE_URL", "sqlite:///app/db/listings.db"))
print(f"\033[35mThe database_url is at {DATABASE_URL}\033[0m")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
SELENIUM_HOST = os.getenv("SELENIUM_HOST", "http://selenium")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
COMMON_PARENT_DOMAIN = os.getenv("COMMON_PARENT_DOMAIN", None)

NO_IMAGE_URL = 'https://i.kym-cdn.com/entries/icons/original/000/049/021/duck_smoking_gif.jpg'

class QueryConfig(BaseModel):
    """Configuration for housing search query parameters. All fields are optional."""
    min_bedrooms: int | None = 4
    min_square_feet: int | None = 1000  
    min_bathrooms: float | None = 2.0
    target_price_bedroom: int | None = 2000

QUERY_CONFIG = QueryConfig(min_bedrooms=4, min_square_feet=1000, min_bathrooms=2.0, target_price_bedroom=2000)

USE_CLAUDE = False

# GPT-4V settings
GPT_MODEL = "gpt-4o-mini"
GPT_TEMPERATURE = 0.5

# Claude 3.5 Sonnet (Upgraded) settings
CLAUDE_MODEL = "claude-3-5-sonnet-20241022"
CLAUDE_TEMPERATURE = 0.5

CRITERIA = """
Housing living requirements: 
1. Nice bathroom 
2. Nice neighborhood immediately by a park 
3. CO2 well regulated and air circulates well 
4. Good light 
5. MAJOR common room that we can set up to be conducive for working. 
6. Bidet (nice to have) 
7. Good temperature control. 
8. High ceilings (nice to have) 
9. Strong shower pressure (helps with hair) 
10. I personally have a closet in my room. If these are guaranteed then good space doesn't even need to be that big
"""