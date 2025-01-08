import { useState, useEffect, useRef } from 'react';
import { API_BASE_URL } from '../services/config';

interface InputModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

interface JobInput {
  name: string;
  min_bedrooms: number;
  min_square_feet: number;
  min_bathrooms: number;
  target_price_bedroom: number;
  criteria?: string;
  location?: string;
  zipcode?: string;
  search_distance_miles?: number;
}

function InputModal({ onClose, onSuccess }: InputModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const [locations, setLocations] = useState<string[]>([]);
  const [formData, setFormData] = useState<JobInput>({
    name: '',
    min_bedrooms: 4,
    min_square_feet: 1000,
    min_bathrooms: 2.0,
    target_price_bedroom: 2000,
    criteria: '',
    location: '',
    zipcode: '',
    search_distance_miles: 10,
  });

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/craiglist/hostnames`, {
          credentials: 'include',
        });
        if (!response.ok) throw new Error('Failed to fetch locations');
        const data = await response.json();
        setLocations(data);
      } catch (error) {
        console.error('Error fetching locations:', error);
      }
    };

    fetchLocations();
  }, []);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
        onClose();
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate required fields
    if (!formData.name || !formData.location) {
      alert('Please fill in all required fields');
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/jobs/add`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(formData),
      });

      if (!response.ok) throw new Error('Failed to create job');
      onSuccess();
    } catch (error) {
      console.error('Error creating job:', error);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: ['min_bedrooms', 'min_square_feet', 'min_bathrooms', 'target_price_bedroom', 'search_distance_miles'].includes(name)
        ? Number(value)
        : value,
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div ref={modalRef} className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-2xl font-bold mb-4">Create New Job</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Job Name <span className="text-red-500">*</span>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              />
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Location <span className="text-red-500">*</span>
              <select
                name="location"
                value={formData.location}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                required
              >
                <option value="">Select a location</option>
                {locations.map((location) => (
                  <option key={location} value={location}>
                    {location}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Zipcode (Optional)
              <input
                type="text"
                name="zipcode"
                value={formData.zipcode}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                pattern="[0-9]{5}"
                title="Five digit zip code"
              />
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Search Distance (miles)
              <input
                type="number"
                name="search_distance_miles"
                value={formData.search_distance_miles}
                onChange={handleChange}
                min="1"
                max="100"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Minimum Bedrooms
              <input
                type="number"
                name="min_bedrooms"
                value={formData.min_bedrooms}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Minimum Square Feet
              <input
                type="number"
                name="min_square_feet"
                value={formData.min_square_feet}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Minimum Bathrooms
              <input
                type="number"
                name="min_bathrooms"
                value={formData.min_bathrooms}
                onChange={handleChange}
                step="0.5"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Target Price per Bedroom
              <input
                type="number"
                name="target_price_bedroom"
                value={formData.target_price_bedroom}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              />
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Additional Criteria
              <textarea
                name="criteria"
                value={formData.criteria}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                rows={3}
              />
            </label>
          </div>

          <div className="flex justify-end gap-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-white bg-blue-500 rounded-md hover:bg-blue-600"
            >
              Create Job
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default InputModal;
