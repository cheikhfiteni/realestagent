import hashlib
from models import engine, Listing
from sqlalchemy.orm import sessionmaker

def _listing_hash(text):
    return hashlib.md5(text.encode()).hexdigest()

def get_stored_listing_hashes():
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        return {listing.hash for listing in session.query(Listing).all()}
    finally:
        session.close()
    

def save_listing_to_db(listings: list[Listing]):
    Session = sessionmaker(bind=engine)
    session = Session()

    columns = [
    'hash', 'title', 'bedrooms', 'bathrooms', 'square_footage',
    'post_id', 'description', 'price', 'location', 'neighborhood',
    'image_urls', 'link'
    ]

    for listing in listings:
        existing = session.query(Listing).filter_by(hash=listing.hash).first()

        if not existing:

            listing_data = {
                column: getattr(listing, column)
                for column in columns
            }
            
            new_listing = Listing(
                **listing_data,
                score=0,
                trace=""
            )
            session.add(new_listing)
            session.commit()
    
    session.close()