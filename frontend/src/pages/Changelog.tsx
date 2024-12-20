import { useEffect, useState } from 'react';
import { API_BASE_URL } from '../services/config';

interface ChangelogEntry {
  id: number;
  date: string;
  title: string;
  description: string;
}

function Changelog() {
  const [changes, setChanges] = useState<ChangelogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchChangelog = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/changelog`, {
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to fetch changelog');
        }

        const data = await response.json();
        setChanges(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchChangelog();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="changelog-container">
      <div style={{
        color: '#666666',
        fontSize: '1.75rem',
        marginBottom: '2rem',
        textAlign: 'left',
        maxWidth: '1000px',
        margin: '0 auto'
      }}>
        tldr;
        <br />
        features
        <br />
        <br />
        ----------------------------------------------------------------------------------
      </div>

      <div className="changelog-entries" style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: '2rem',
        padding: '1rem'
      }}>
        {changes.map((entry) => (
          <div 
            key={entry.id} 
            style={{
              backgroundColor: '#f5f5f7',
              borderRadius: '12px',
              padding: '1.5rem',
              boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
              color: '#666666'
            }}
          >
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1rem'
            }}>
              <h3 style={{ margin: 0, fontSize: '1.2rem' }}>{entry.title}</h3>
              <span style={{ fontSize: '0.9rem' }}>
                {new Date(entry.date).toLocaleDateString()}
              </span>
            </div>
            <p style={{ 
              margin: 0,
              fontSize: '1rem',
              lineHeight: '1.5'
            }}>
              {entry.description}
            </p>
          </div>
        ))}
        {changes.length === 0 && (
          <p style={{ color: '#666666' }}>No changelog entries available.</p>
        )}
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginTop: '3rem',
        color: '#666666',
        fontSize: '1rem'
      }}>
        Supported by generous Github sponsors and maintainers at
        <a href="https://github.com/cheikhfiteni/realestagent" style={{ marginLeft: '0.5rem' }}>
          <img src="/src/assets/github-mark.svg" alt="GitHub Sponsors" style={{ width: '16px', height: '16px' }} />
        </a>
      </div>
    </div>
  );
}

export default Changelog;
