import { useEffect, useState } from 'react';

interface Post {
  id: number;
  title: string;
  cover_image_url: string;
  location: string;
  cost: number;
  bedrooms: number;
  bathrooms: number;
  square_footage: number;
  score: number;
  trace: string;
}

function Feed() {
  const [listings, setListings] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchListings = async () => {
      try {
        const response = await fetch('http://localhost:8000/listings', {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch listings');
        }

        const data = await response.json();
        setListings(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchListings();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="feed-container">
      <h1>Property Listings</h1>
      <div className="listings-grid">
        {listings.map((listing) => (
          <div key={listing.id} className="listing-card">
            <img 
              src={listing.cover_image_url} 
              alt={listing.title}
              className="listing-image"
            />
            <div className="listing-details">
              <h2>{listing.title}</h2>
              <p className="location">{listing.location}</p>
              <p className="price">${listing.cost.toLocaleString()}</p>
              <div className="property-stats">
                <span>{listing.bedrooms} beds</span>
                <span>{listing.bathrooms} baths</span>
                <span>{listing.square_footage.toLocaleString()} sq ft</span>
              </div>
              <div className="score-container">
                <span className="score">Score: {listing.score}</span>
                <span className="trace">Trace: {listing.trace}</span>
              </div>
            </div>
          </div>
        ))}
        {listings.length === 0 && (
          <p>No listings available.</p>
        )}
      </div>
    </div>
  );
}

export default Feed;

