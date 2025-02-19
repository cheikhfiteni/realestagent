from datetime import datetime
from sqlalchemy import Boolean, create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.config import DATABASE_URL

Base = declarative_base()

class JobTemplate(Base):
    __tablename__ = 'job_templates'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    min_bedrooms = Column(Integer, nullable=True)
    min_square_feet = Column(Integer, nullable=True)
    min_bathrooms = Column(Float, nullable=True)
    target_price_bedroom = Column(Integer, nullable=True)
    criteria = Column(String, nullable=True)
    location = Column(String, nullable=True)
    zipcode = Column(String, nullable=True)
    search_distance_miles = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class JobListingScore(Base):
    __tablename__ = 'job_listing_scores'
    
    job_id = Column(UUID(as_uuid=True), ForeignKey('jobs.id'), primary_key=True)
    listing_id = Column(UUID(as_uuid=True), ForeignKey('listings.id'), primary_key=True)
    score = Column(Float, nullable=False, default=0)
    trace = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    job = relationship("Job", back_populates="listing_scores")

class Job(Base):
    __tablename__ = 'jobs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    template_id = Column(UUID(as_uuid=True), ForeignKey('job_templates.id'))
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    template = relationship("JobTemplate", lazy="joined")
    user = relationship("User", lazy="selectin")
    listing_scores = relationship("JobListingScore", back_populates="job", cascade="all, delete-orphan")

class Listing(Base):
    __tablename__ = 'listings'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
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

    def __repr__(self):
        return f"<Listing(title='{self.title}', price=${self.price}, {self.bedrooms}BR/{self.bathrooms}BA, location='{self.location}', neighborhood='{self.neighborhood}')>"
    
class VerificationCode(Base):
    __tablename__ = "verification_codes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, index=True)
    code = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)

# Create database engine and tables
engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
