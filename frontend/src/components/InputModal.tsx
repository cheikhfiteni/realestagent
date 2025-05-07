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
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center p-4 animate-fadeIn">
      <div ref={modalRef} className="bg-card text-card-foreground rounded-lg shadow-xl p-6 w-full max-w-xl animate-dropFadeIn">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-primary">Create New Job</h2>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Close modal"
          >
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Job Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-muted-foreground mb-1">
              Job Name <span className="text-destructive">*</span>
            </label>
            <input
              id="name"
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border-border bg-input text-foreground shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 h-10 px-3"
              required
            />
          </div>

          {/* Location and Zipcode - Grouped */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="location" className="block text-sm font-medium text-muted-foreground mb-1">
                Location <span className="text-destructive">*</span>
              </label>
              <select
                id="location"
                name="location"
                value={formData.location}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-border bg-input text-foreground shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 h-10 px-3"
                required
              >
                <option value="">Select a location</option>
                {locations.map((location) => (
                  <option key={location} value={location}>
                    {location}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="zipcode" className="block text-sm font-medium text-muted-foreground mb-1">
                Zipcode (Optional)
              </label>
              <input
                id="zipcode"
                type="text"
                name="zipcode"
                value={formData.zipcode}
                onChange={handleChange}
                className="mt-1 block w-full rounded-md border-border bg-input text-foreground shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 h-10 px-3"
                pattern="[0-9]{5}"
                title="Five digit zip code"
              />
            </div>
          </div>
          
          {/* Search Distance */}
           <div>
            <label htmlFor="search_distance_miles" className="block text-sm font-medium text-muted-foreground mb-1">
              Search Distance (miles)
            </label>
            <input
              id="search_distance_miles"
              type="number"
              name="search_distance_miles"
              value={formData.search_distance_miles ?? ''}
              onChange={handleChange}
              onBlur={handleBlur}
              min="1"
              max="100"
              className="mt-1 block w-full rounded-md border-border bg-input text-foreground shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 h-10 px-3"
            />
          </div>

          {/* Numerical Inputs - Grouped */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="min_bedrooms" className="block text-sm font-medium text-muted-foreground mb-1">
                Min Bedrooms
              </label>
              <input
                id="min_bedrooms"
                type="number"
                name="min_bedrooms"
                value={formData.min_bedrooms ?? ''}
                onChange={handleChange}
                onBlur={handleBlur}
                className="mt-1 block w-full rounded-md border-border bg-input text-foreground shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 h-10 px-3"
              />
            </div>
            <div>
              <label htmlFor="min_bathrooms" className="block text-sm font-medium text-muted-foreground mb-1">
                Min Bathrooms
              </label>
              <input
                id="min_bathrooms"
                type="number"
                name="min_bathrooms"
                value={formData.min_bathrooms ?? ''}
                onChange={handleChange}
                onBlur={handleBlur}
                step="0.5"
                className="mt-1 block w-full rounded-md border-border bg-input text-foreground shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 h-10 px-3"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label htmlFor="min_square_feet" className="block text-sm font-medium text-muted-foreground mb-1">
                Min Square Feet
              </label>
              <input
                id="min_square_feet"
                type="number"
                name="min_square_feet"
                value={formData.min_square_feet ?? ''}
                onChange={handleChange}
                onBlur={handleBlur}
                className="mt-1 block w-full rounded-md border-border bg-input text-foreground shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 h-10 px-3"
              />
            </div>
             <div>
              <label htmlFor="target_price_bedroom" className="block text-sm font-medium text-muted-foreground mb-1">
                Target Price/Bedroom
              </label>
              <input
                id="target_price_bedroom"
                type="number"
                name="target_price_bedroom"
                value={formData.target_price_bedroom ?? ''}
                onChange={handleChange}
                onBlur={handleBlur}
                className="mt-1 block w-full rounded-md border-border bg-input text-foreground shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50 h-10 px-3"
              />
            </div>
          </div>

          {/* Additional Criteria */}
          <div>
            <label htmlFor="criteria" className="block text-sm font-medium text-muted-foreground mb-1">
              Additional Criteria
            </label>
            <textarea
              id="criteria"
              name="criteria"
              value={formData.criteria}
              onChange={handleChange}
              className="mt-1 block w-full rounded-md border-border bg-input text-foreground shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-50"
              rows={3}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end gap-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-muted-foreground bg-muted rounded-md hover:bg-accent hover:text-accent-foreground transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded-md hover:bg-primary/90 transition-colors"
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
