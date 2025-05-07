import { API_BASE_URL } from '@/services/config';
import { useState } from 'react';
import { toast } from 'react-hot-toast';

interface InviteModalProps {
  jobId: string;
  onClose: () => void;
  onInviteSent: () => void;
}

function InviteModal({ jobId, onClose, onInviteSent }: InviteModalProps) {
  const [inviteEmail, setInviteEmail] = useState('');

  const handleSendInvitation = async () => {
    console.log("Sending invitation...");
    if (!inviteEmail) {
      toast.error('Please enter an email address.');
      return;
    }

    const toastId = toast.loading('Sending invitation...');
    try {
      const response = await fetch(`${API_BASE_URL}/jobs/${jobId}/invite`, {
        credentials: 'include',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: inviteEmail }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Failed to send invitation');
      }

      toast.success(result.message || 'Invitation sent successfully!', { id: toastId });
      setInviteEmail('');
      onInviteSent(); // Call this to potentially refresh data or close modal via parent
      onClose(); // Close the modal
    } catch (error: any) {
      toast.error(error.message || 'Failed to send invitation', { id: toastId });
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white p-6 rounded-lg shadow-xl w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">Invite User to Job</h2>
        <label htmlFor="invite-email" className="block text-sm font-medium text-gray-700 mb-1">
          User's Email:
        </label>
        <input
          type="email"
          id="invite-email"
          value={inviteEmail}
          onChange={(e) => setInviteEmail(e.target.value)}
          placeholder="user@example.com"
          className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 mb-4"
        />
        <div className="flex justify-end gap-2">
          <button
            onClick={onClose}
            className="bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSendInvitation}
            className="bg-green-500 text-white px-4 py-2 rounded-md hover:bg-green-600 transition-colors"
          >
            Send Invitation
          </button>
        </div>
      </div>
    </div>
  );
}

export default InviteModal; 