import { useState, useEffect, useRef } from 'react';

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
}

const isValidJobInput = (data: any): data is JobInput => {
  return (
    typeof data.name === 'string' &&
    typeof data.min_bedrooms === 'number' &&
    typeof data.min_square_feet === 'number' &&
    typeof data.min_bathrooms === 'number' &&
    typeof data.target_price_bedroom === 'number' &&
    (data.criteria === undefined || typeof data.criteria === 'string')
  );
};

function InputModal({ onClose, onSuccess }: InputModalProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const [formData, setFormData] = useState<JobInput>({
    name: '',
    min_bedrooms: 4,
    min_square_feet: 1000,
    min_bathrooms: 2.0,
    target_price_bedroom: 2000,
    criteria: '',
  });

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
    
    // Log the type validation result
    console.log('Is valid job input:', isValidJobInput(formData));
    console.log('Form data types:', {
        name: typeof formData.name,
        min_bedrooms: typeof formData.min_bedrooms,
        min_square_feet: typeof formData.min_square_feet,
        min_bathrooms: typeof formData.min_bathrooms,
        target_price_bedroom: typeof formData.target_price_bedroom,
        criteria: typeof formData.criteria,
    });
    console.log('Raw form data:', formData);

    try {
      const response = await fetch('http://localhost:8000/jobs/add', {
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

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: ['min_bedrooms', 'min_square_feet', 'min_bathrooms', 'target_price_bedroom'].includes(name)
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
              Job Name
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
