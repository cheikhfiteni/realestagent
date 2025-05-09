import { useState, useEffect } from 'react';
import { Add, Cloud, UserFollow } from '@carbon/icons-react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import InputModal from '../components/InputModal';
import InviteModal from '../components/InviteModal';
import { fetchJobs, invalidateJobsCache, type Job } from '../services/jobs';
import Header from '../components/Header';

function getTimeAgo(date: string) {
  const now = new Date();
  const updated = new Date(date);
  const diffMinutes = Math.floor((now.getTime() - updated.getTime()) / (1000 * 60));
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMinutes < 60) {
    return `${diffMinutes} minutes ago`;
  } else if (diffHours < 48) {
    return `${diffHours} hours ago`;
  } else {
    return `${diffDays} days ago`;
  }
}

function Overview() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isAddJobModalOpen, setIsAddJobModalOpen] = useState(false);
  const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);
  const [selectedJobIdForInvite, setSelectedJobIdForInvite] = useState<string | null>(null);
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
    setIsAddJobModalOpen(false);
    invalidateJobsCache();
    loadJobs();
    toast.success('Job added successfully');
  };

  const handleOpenInviteModal = (jobId: string) => {
    setSelectedJobIdForInvite(jobId);
    setIsInviteModalOpen(true);
  };

  const handleCloseInviteModal = () => {
    setIsInviteModalOpen(false);
    setSelectedJobIdForInvite(null);
  };

  const handleInviteSent = () => {
    // Optionally, you can add logic here if needed after an invite is sent,
    // like a specific toast or data refresh if not handled by loadJobs.
    // For now, closing the modal is handled by the modal itself.
  };

  return (
    <>
      <div className="w-[95vw] px-12 flex-none py-4">
        <Header />
      </div>
      <div className="w-full flex justify-center">
        <div className="w-[60%]">
          <h1 className="text-3xl font-bold text-center mt-5 mb-8 border-b-2 pb-2 delayed-fade-in-2">
            Overview of All Jobs
          </h1>
          
          <div className="flex justify-end mb-6">
            <button
              onClick={() => setIsAddJobModalOpen(true)}
              className="flex items-center gap-2 bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600 transition-colors"
            >
              <Add size={20} /> Add New Job
            </button>
          </div>

          <div className="flex flex-col gap-6">
            {jobs.map((job) => (
              <div
                key={job.id}
                onClick={() => handleJobClick(job.id)}
                className="flex bg-white slide-in rounded-lg cursor-pointer hover:bg-gray-50 transition-all border border-dotted border-gray-300 shadow-md hover:shadow-lg p-5 overflow-hidden"
              >
                <div className="flex flex-col md:flex-row gap-12 w-full">
                  <div className="relative w-full md:w-72 h-36 flex-shrink-0">
                    {/* Back image */}
                    <div className="absolute inset-0 -left-6 -top-3 bg-gray-50 rounded-lg transform translate-x-6 translate-y-6 -z-20" />
                    {/* Middle image */}
                    <div className="absolute inset-0 -left-3 -top-1.5 bg-gray-100 rounded-lg transform translate-x-3 translate-y-3 -z-10" />
                    {/* Front image */}
                    <div className="absolute inset-0 bg-gray-200 rounded-lg overflow-hidden">
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
                  <div className="flex flex-col flex-grow justify-between">
                    <div className="flex justify-between items-start gap-24">
                      <h3 className="text-2xl font-semibold">{job.name}</h3>
                      <div className="flex items-center gap-2 text-gray-600 text-sm whitespace-nowrap">
                        <Cloud size={16} />
                        <span className="hidden sm:inline">Updated</span>
                        <span>{getTimeAgo(job.last_updated)}</span>
                      </div>
                    </div>
                    <div className="flex justify-end">
                      <span className="text-sm text-gray-500 bg-gray-100 px-3 py-1 rounded-full">
                        {job.listing_count || 0} Listings
                      </span>
                      <button
                        onClick={(e) => { e.stopPropagation(); handleOpenInviteModal(job.id); }}
                        className="ml-4 p-2 rounded-full hover:bg-gray-200 transition-colors"
                        title="Invite user to this job"
                      >
                        <UserFollow size={20} className="text-blue-500" />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {isAddJobModalOpen && (
            <InputModal
              onClose={() => setIsAddJobModalOpen(false)}
              onSuccess={handleAddJobSuccess}
            />
          )}

          {isInviteModalOpen && selectedJobIdForInvite && (
            <InviteModal
              jobId={selectedJobIdForInvite}
              onClose={handleCloseInviteModal}
              onInviteSent={handleInviteSent}
            />
          )}
        </div>
      </div>
    </>
  );
}

export default Overview;
