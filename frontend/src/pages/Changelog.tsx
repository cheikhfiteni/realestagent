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

        let data = await response.json();
        // Sort entries by date in descending order (newest first)
        data.sort((a: ChangelogEntry, b: ChangelogEntry) => new Date(b.date).getTime() - new Date(a.date).getTime());
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
    return <div style={{ textAlign: 'center', padding: '2rem', fontSize: '1.2rem', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading...</div>;
  }

  if (error) {
    return <div style={{ textAlign: 'center', padding: '2rem', color: 'red', height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Error: {error}</div>;
  }

  return (
    <div style={{ 
      fontFamily: "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif", 
      color: '#333',
      //padding: '2rem', // Remove padding from here to allow full width for children
      maxWidth: '800px', // Keep max width for overall content centering
      margin: '0 auto',
      display: 'flex',
      flexDirection: 'column',
      height: 'calc(100vh - 4rem)', // Adjust based on your app's global header/nav if any, or use 100vh
      boxSizing: 'border-box',
      padding: '2rem 0' // Add vertical padding
    }}>
      <header style={{ 
        marginBottom: '1.5rem', // Reduced margin
        textAlign: 'center', 
        padding: '0 2rem' // Add horizontal padding here
      }}>
        <h1 style={{ 
          fontSize: '2.2rem', // Slightly smaller
          color: '#2c3e50', 
          fontWeight: 600,
          //borderBottom: '2px solid #3498db', // Optional: can be removed for flatter design
          paddingBottom: '0.5rem',
          display: 'inline-block',
          marginBlockEnd: '0.5em' // Adjusted margin
        }}>
          What's New
        </h1>
        <p style={{ fontSize: '1rem', color: '#7f8c8d', marginTop: '0.25rem' }}>
          Latest updates, features, and improvements.
        </p>
      </header>

      {changes.length === 0 && !loading && (
        <div style={{ flexGrow: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '0 2rem' }}>
          <p style={{ textAlign: 'center', color: '#666666', fontSize: '1.1rem' }}>
            No changelog entries available at the moment. Check back soon!
          </p>
        </div>
      )}

      <div style={{ 
        flexGrow: 1, 
        overflowY: 'auto', 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '0rem', // No gap, borders will separate
        padding: '0 2rem' // Add horizontal padding here
        // Custom scrollbar (optional, webkit only)
        // scrollbarWidth: 'thin', 
        // scrollbarColor: '#3498db #ecf0f1'
      }}>
        {changes.map((entry, index) => (
          <article 
            key={entry.id} 
            style={{
              backgroundColor: '#ffffff',
              //borderRadius: '8px', // Flatter design
              padding: '1.5rem 0.5rem', // Adjusted padding
              //boxShadow: '0 6px 12px rgba(0, 0, 0, 0.08)', // Removed shadow for flatter design
              //borderLeft: '5px solid #3498db', // Removed side accent
              borderBottom: index === changes.length - 1 ? 'none' : '1px solid #ecf0f1', // Separator line
              width: '100%' // Ensure it fills width
            }}
          >
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start', // Align items to start for better text flow
              marginBottom: '0.75rem', // Reduced margin
              //borderBottom: '1px solid #ecf0f1', // Moved to article style
              //paddingBottom: '1rem' // Removed, using article padding
            }}>
              <h2 style={{ 
                margin: 0, 
                fontSize: '1.3rem', // Slightly smaller
                color: '#2980b9',
                fontWeight: 500 
              }}>
                {entry.title}
              </h2>
              <time dateTime={entry.date} style={{ 
                fontSize: '0.85rem', // Slightly smaller
                color: '#7f8c8d', 
                fontStyle: 'italic',
                whiteSpace: 'nowrap', // Prevent date from wrapping awkwardly
                marginLeft: '1rem' // Add some space between title and date
              }}>
                {new Date(entry.date).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
              </time>
            </div>
            <p style={{ 
              margin: 0,
              fontSize: '0.95rem', // Slightly smaller
              lineHeight: '1.6',
              color: '#555'
            }}>
              {entry.description}
            </p>
          </article>
        ))}
      </div>

      <div style={{ // Restored user's preferred footer structure and styling
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        marginTop: '1.5rem', // Reduced margin
        color: '#666666',
        fontSize: '1rem',
        padding: '1rem 2rem 0', // Add padding, especially top
        borderTop: '1px solid #ecf0f1' // Added a top border for separation
      }}>
        Supported by generous Github sponsors and maintainers at
        <a 
          href="https://github.com/cheikhfiteni/realestagent" 
          target="_blank" 
          rel="noopener noreferrer" 
          style={{ 
            marginLeft: '0.5rem', 
            color: '#3498db', // Keep consistent link color
            textDecoration: 'none'
            // fontWeight: 500 // Optional: can remove if default is fine
          }}
        >
          {/* RealestAgent GitHub // User preferred only icon */}
          <img 
            src="/src/assets/github-mark.svg" 
            alt="GitHub Sponsors" // Changed alt text to be more accurate to original intent
            style={{ 
              width: '16px', 
              height: '16px', 
              // marginLeft: '0.3rem', // Handled by link's margin
              verticalAlign: 'middle'
            }} 
          />
        </a>
      </div>
    </div>
  );
}

export default Changelog;
