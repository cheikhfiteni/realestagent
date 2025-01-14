import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Cloud } from '@carbon/icons-react';
import { toast } from 'react-hot-toast';
import { API_BASE_URL } from '../services/config';
import { getJob } from '../services/jobs';

interface Post {
  id: string;
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

  const job = jobId ? getJob(jobId) : null;

  useEffect(() => {
    const fetchListings = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`, {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch listings');
        }

        const data = await response.json();
        console.log('Fetched listings:', data);
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

  const handleListingClick = (e: React.MouseEvent, link: string) => {
    e.preventDefault();
    e.stopPropagation();
    
    console.log('Handling listing click, full listing:', listings.find(l => l.link === link));
    
    if (!link || link === 'undefined') {
      console.log('No link available');
      toast.error('No link available for this listing');
      return;
    }

    try {
      console.log('Opening link in new tab:', link);
      window.open(link, '_blank', 'noopener,noreferrer');
    } catch (error) {
      console.error('Error opening link:', error);
      toast.error('Failed to open listing');
    }
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
          <h1 className="text-3xl font-bold">[ {job?.name || 'Loading...'} ]</h1>
          <span className="w-3 h-3 bg-green-500 rounded-full"></span>
        </div>
        <div className="flex items-center gap-2 text-gray-600 mt-2">
          <Cloud size={20} />
          {job ? (
            <span>Time last synced: {new Date(job.last_updated).toLocaleString()}</span>
          ) : (
            <span>No sync data available</span>
          )}
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

      <div className="flex flex-col gap-6 max-w-6xl mx-auto">
        {sortedListings.map((listing) => (
          <div
            key={listing.id}
            className="flex bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer overflow-hidden h-64"
          >
            <a
              href={listing.link}
              onClick={(e) => handleListingClick(e, listing.link)}
              className="flex w-full"
              target="_blank"
              rel="noopener noreferrer"
            >
              <div className="w-96 flex-shrink-0">
                <img 
                  src={listing.cover_image_url} 
                  alt={listing.title}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="flex-grow p-6 flex flex-col">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h2 className="text-2xl font-semibold mb-2">{listing.title}</h2>
                    <p className="text-gray-600">{listing.location}</p>
                  </div>
                  <p className="text-2xl font-bold text-green-600">
                    ${listing.cost.toLocaleString()}
                  </p>
                </div>
                
                <div className="flex gap-6 text-gray-600 mb-4">
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

                <div className="mt-auto">
                  <div className="text-gray-500 text-sm line-clamp-2 mb-3">
                    {listing.trace}
                  </div>
                  <div className="pt-3 border-t">
                    <span className="text-blue-600 font-medium text-lg">
                      Score: {listing.score.toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>
            </a>
          </div>
        ))}
        {listings.length === 0 && (
          <p className="text-center py-8 text-gray-500">No listings available.</p>
        )}
      </div>
    </div>
  );
}

export default Feed;

