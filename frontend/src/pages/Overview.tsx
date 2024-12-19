import { useState, useEffect } from 'react';
import { Add, Cloud } from '@carbon/icons-react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import InputModal from '../components/InputModal';

interface Job {
  id: number;
  name: string;
  last_updated: string;
  // Add other job properties as needed
}

function Overview() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const navigate = useNavigate();

  const fetchJobs = async () => {
    try {
      const response = await fetch('http://localhost:8000/jobs', {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Failed to fetch jobs');
      const data = await response.json();
      setJobs(data);
    } catch (error) {
      toast.error('Failed to fetch jobs');
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleJobClick = (jobId: number) => {
    navigate(`/feed/${jobId}`);
  };

  const handleAddJobSuccess = () => {
    setIsModalOpen(false);
    fetchJobs();
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {jobs.map((job) => (
          <div
            key={job.id}
            onClick={() => handleJobClick(job.id)}
            className="border-2 border-dotted p-4 rounded-lg cursor-pointer hover:bg-gray-50 transition-all"
          >
            <h3 className="text-xl font-semibold mb-2">{job.name}</h3>
            <div className="flex items-center gap-2 text-gray-600">
              <Cloud size={16} />
              <span>Last Updated: {new Date(job.last_updated).toLocaleString()}</span>
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
