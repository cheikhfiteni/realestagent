from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Listing(Base):
    __tablename__ = 'listings'

    id = Column(Integer, primary_key=True)
    hash = Column(String, unique=True, nullable=False)
    title = Column(String)
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    square_footage = Column(Integer)
    post_id = Column(String, unique=True)
    description = Column(String)
    price = Column(Integer)
    location = Column(String)
    neighborhood = Column(String)
    image_urls = Column(String)  # Stored as JSON string array
    link = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    score = Column(Integer, nullable=True, default=None)
    trace = Column(String, nullable=True, default=None)

    def __repr__(self):
        return f"<Listing(title='{self.title}', price=${self.price}, {self.bedrooms}BR/{self.bathrooms}BA, score={self.score}, location='{self.location}', neighborhood='{self.neighborhood}')>"

# Create database engine and tables
engine = create_engine(f'sqlite:///listings.db')
Base.metadata.create_all(engine)
