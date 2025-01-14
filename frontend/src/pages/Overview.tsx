import { useState, useEffect } from 'react';
import { Add, Cloud } from '@carbon/icons-react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import InputModal from '../components/InputModal';
import { fetchJobs, invalidateJobsCache, type Job } from '../services/jobs';

function Overview() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const navigate = useNavigate();

  const loadJobs = async () => {
    try {
      const data = await fetchJobs();
      setJobs(data);
    } catch (error) {
      toast.error('Failed to fetch jobs');
    }
  };

  useEffect(() => {
    loadJobs();
  }, []);

  const handleJobClick = (jobId: string) => {
    navigate(`/feed/${jobId}`);
  };

  const handleAddJobSuccess = () => {
    setIsModalOpen(false);
    invalidateJobsCache();
    loadJobs();
    toast.success('Job added successfully');
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold text-center mb-8 border-b-2 pb-2">
        Overview of All Jobs
      </h1>
      
      <div className="flex justify-end mb-6">
        <button
          onClick={() => setIsModalOpen(true)}
          className="flex items-center gap-2 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
        >
          <Add size={20} /> Add New Job
        </button>
      </div>

      <div className="flex flex-col gap-4">
        {jobs.map((job) => (
          <div
            key={job.id}
            onClick={() => handleJobClick(job.id)}
            className="flex items-center p-6 border rounded-lg cursor-pointer hover:bg-gray-50 transition-all w-full max-w-7xl mx-auto"
          >
            <div className="flex items-center gap-12 w-full">
              <div className="relative w-72 h-40 flex-shrink-0">
                {/* Stacked effect images - back to front */}
                <div className="absolute inset-0 -left-6 top-0 bg-gray-50 rounded-lg -z-20 transform rotate-1" />
                <div className="absolute inset-0 -left-3 top-0 bg-gray-100 rounded-lg -z-10 transform rotate-0.5" />
                {/* Main image - most offset to bottom-right */}
                <div className="absolute inset-0 left-0 top-0 bg-gray-200 rounded-lg overflow-hidden transform rotate-0">
                  {job.cover_image_url ? (
                    <img
                      src={job.cover_image_url}
                      alt={job.name}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full bg-gray-300" />
                  )}
                </div>
              </div>
              <div className="flex flex-col gap-3 flex-grow">
                <h3 className="text-2xl font-semibold">{job.name}</h3>
                <div className="flex items-center gap-2 text-gray-600">
                  <Cloud size={16} />
                  <span>Last Updated: {new Date(job.last_updated).toLocaleString()}</span>
                </div>
                <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full w-fit">
                  {job.listing_count || 0} Listings
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {isModalOpen && (
        <InputModal
          onClose={() => setIsModalOpen(false)}
          onSuccess={handleAddJobSuccess}
        />
      )}
    </div>
  );
}

export default Overview;
