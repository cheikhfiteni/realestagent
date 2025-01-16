import { useState, useEffect, useRef } from 'react';
import { API_BASE_URL } from '../services/config';
import { toast } from 'react-hot-toast';

interface InputModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

interface JobInput {
  name: string;
  min_bedrooms: number | null;
  min_square_feet: number | null;
  min_bathrooms: number | null;
  target_price_bedroom: number | null;
  criteria?: string;
  location?: string;
  zipcode?: string;
  search_distance_miles: number | null;
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

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    
    if (['min_bedrooms', 'min_square_feet', 'search_distance_miles', 'target_price_bedroom'].includes(name)) {
      // Only allow positive integers for these fields
      if (value === '') {
        setFormData(prev => ({ ...prev, [name]: null }));
      } else {
        const numValue = parseInt(value);
        if (!isNaN(numValue) && numValue >= 0) {
          setFormData(prev => ({ ...prev, [name]: numValue }));
        } else {
          toast.error(`${name.split('_').join(' ')} must be a positive number`);
        }
      }
    } else if (name === 'min_bathrooms') {
      // Allow decimals for bathrooms
      if (value === '') {
        setFormData(prev => ({ ...prev, [name]: null }));
      } else {
        const numValue = parseFloat(value);
        if (!isNaN(numValue) && numValue >= 0) {
          setFormData(prev => ({ ...prev, [name]: numValue }));
        } else {
          toast.error('Bathrooms must be a positive number');
        }
      }
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const { name } = e.target;
    if (['min_bedrooms', 'min_square_feet', 'min_bathrooms', 'target_price_bedroom', 'search_distance_miles'].includes(name)) {
      if (formData[name as keyof JobInput] === null) {
        setFormData(prev => ({ ...prev, [name]: 0 }));
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate required fields
    if (!formData.name || !formData.location) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (formData.zipcode && !/^\d{5}$/.test(formData.zipcode)) {
      toast.error('Zipcode must be 5 digits');
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
      toast.success('Job created successfully');
      onSuccess();
    } catch (error) {
      console.error('Error creating job:', error);
      toast.error('Failed to create job');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
      <div ref={modalRef} className="bg-gray-50 rounded-lg p-6 w-full max-w-md">
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
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-black h-10"
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
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-black h-10"
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
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-black h-10"
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
                value={formData.search_distance_miles ?? ''}
                onChange={handleChange}
                onBlur={handleBlur}
                min="1"
                max="100"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-black h-10"
              />
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Minimum Bedrooms
              <input
                type="number"
                name="min_bedrooms"
                value={formData.min_bedrooms ?? ''}
                onChange={handleChange}
                onBlur={handleBlur}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-black h-10"
              />
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Minimum Square Feet
              <input
                type="number"
                name="min_square_feet"
                value={formData.min_square_feet ?? ''}
                onChange={handleChange}
                onBlur={handleBlur}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-black h-10"
              />
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Minimum Bathrooms
              <input
                type="number"
                name="min_bathrooms"
                value={formData.min_bathrooms ?? ''}
                onChange={handleChange}
                onBlur={handleBlur}
                step="0.5"
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-black h-10"
              />
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">
              Target Price per Bedroom
              <input
                type="number"
                name="target_price_bedroom"
                value={formData.target_price_bedroom ?? ''}
                onChange={handleChange}
                onBlur={handleBlur}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-black h-10"
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
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 bg-white text-black"
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
