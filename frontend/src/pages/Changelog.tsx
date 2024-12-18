import { useEffect, useState } from 'react';

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
        const response = await fetch('http://localhost:8000/changelog', {
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
      <h1>Changelog</h1>
      <div className="changelog-entries">
        {changes.map((entry) => (
          <div key={entry.id} className="changelog-entry">
            <div className="entry-header">
              <h2>{entry.title}</h2>
              <span className="entry-date">{new Date(entry.date).toLocaleDateString()}</span>
            </div>
            <p className="entry-description">{entry.description}</p>
          </div>
        ))}
        {changes.length === 0 && (
          <p>No changelog entries available.</p>
        )}
      </div>
    </div>
  );
}

export default Changelog;
