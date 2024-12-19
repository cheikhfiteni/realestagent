import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Cloud } from '@carbon/icons-react';
import { toast } from 'react-hot-toast';

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
  link: string;
  last_updated: string;
}

type SortField = keyof Omit<Post, 'cover_image_url' | 'id'>;
type SortDirection = 'asc' | 'desc';

function Feed() {
  const { jobId } = useParams<{ jobId: string }>();
  const [listings, setListings] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('cost');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  useEffect(() => {
    const fetchListings = async () => {
      try {
        const response = await fetch(`http://localhost:8000/jobs/${jobId}`, {
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
  }, [jobId]);

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortedListings = [...listings].sort((a, b) => {
    const aValue = a[sortField];
    const bValue = b[sortField];
    
    if (typeof aValue === 'string' && typeof bValue === 'string') {
      return sortDirection === 'asc' 
        ? aValue.localeCompare(bValue)
        : bValue.localeCompare(aValue);
    }
    
    return sortDirection === 'asc'
      ? (aValue as number) - (bValue as number)
      : (bValue as number) - (aValue as number);
  });

  const handleListingClick = (link: string) => {
    if (!link) {
      toast.error('No link available for this listing');
      return;
    }
    window.open(link, '_blank');
  };

  if (loading) {
    return <div className="flex justify-center items-center h-screen">Loading...</div>;
  }

  if (error) {
    return <div className="text-red-500 text-center p-4">Error: {error}</div>;
  }

  const SortButton = ({ field }: { field: SortField }) => (
    <button
      onClick={() => handleSort(field)}
      className="px-3 py-1 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded"
    >
      {field.charAt(0).toUpperCase() + field.slice(1)}
      {sortField === field && (
        <span className="ml-1">
          {sortDirection === 'asc' ? '↑' : '↓'}
        </span>
      )}
    </button>
  );

  return (
    <div className="p-6">
      <div className="mb-8">
        <div className="flex items-center gap-2">
          <h1 className="text-3xl font-bold">Job Results</h1>
          <span className="w-3 h-3 bg-green-500 rounded-full"></span>
        </div>
        <div className="flex items-center gap-2 text-gray-600 mt-2">
          <Cloud size={20} />
          <span>Time last synced: {new Date(listings[0]?.last_updated || '').toLocaleString()}</span>
        </div>
      </div>

      <div className="mb-4 flex gap-4 border-b pb-4">
        <SortButton field="title" />
        <SortButton field="location" />
        <SortButton field="cost" />
        <SortButton field="bedrooms" />
        <SortButton field="bathrooms" />
        <SortButton field="square_footage" />
        <SortButton field="score" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedListings.map((listing) => (
          <div
            key={listing.id}
            onClick={() => handleListingClick(listing.link)}
            className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer overflow-hidden"
          >
            <img 
              src={listing.cover_image_url} 
              alt={listing.title}
              className="w-full h-48 object-cover"
            />
            <div className="p-4">
              <h2 className="text-xl font-semibold mb-2">{listing.title}</h2>
              <p className="text-gray-600 mb-2">{listing.location}</p>
              <p className="text-2xl font-bold text-green-600 mb-3">
                ${listing.cost.toLocaleString()}
              </p>
              <div className="grid grid-cols-3 gap-2 text-sm text-gray-600">
                <div>
                  <span className="font-medium">{listing.bedrooms}</span> beds
                </div>
                <div>
                  <span className="font-medium">{listing.bathrooms}</span> baths
                </div>
                <div>
                  <span className="font-medium">{listing.square_footage.toLocaleString()}</span> sqft
                </div>
              </div>
              <div className="mt-3 pt-3 border-t">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-blue-600 font-medium">
                    Score: {listing.score.toFixed(2)}
                  </span>
                  <span className="text-gray-500">{listing.trace}</span>
                </div>
              </div>
            </div>
          </div>
        ))}
        {listings.length === 0 && (
          <p className="text-center col-span-3 py-8 text-gray-500">No listings available.</p>
        )}
      </div>
    </div>
  );
}

export default Feed;

