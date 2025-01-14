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
    <div className="p-6 max-w-5xl mx-auto">
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
            className="flex items-center justify-between p-4 border rounded-lg cursor-pointer hover:bg-gray-50 transition-all w-full"
          >
            <div className="flex items-center gap-8">
              <h3 className="text-xl font-semibold min-w-[200px]">{job.name}</h3>
              <div className="flex items-center gap-2 text-gray-600">
                <Cloud size={16} />
                <span>Last Updated: {new Date(job.last_updated).toLocaleString()}</span>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                {job.listing_count || 0} Listings
              </span>
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
