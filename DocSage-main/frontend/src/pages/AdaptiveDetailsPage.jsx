import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import '../Styles/dashboard.css';

export default function AdaptiveDetailsPage() {
    const [details, setDetails] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const { fileHash } = useParams(); // Gets the fileHash from the URL

    useEffect(() => {
        const token = localStorage.getItem('docsage_token');
        let isCancelled = false; // Flag to prevent errors if you navigate away

        const fetchDetails = async () => {
            // Stop polling if the component has been unmounted or there's no hash
            if (isCancelled || !fileHash) return;

            try {
                const res = await fetch('http://localhost:8004/llm/extract-adaptive', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}` 
                    },
                    body: JSON.stringify({ file_hash: fileHash })
                });

                if (!res.ok) {
                    const errData = await res.json();
                    throw new Error(errData.detail || 'Failed to fetch details');
                }

                const data = await res.json();

                if (data.status === 'processing') {
                    // If the backend is still working, wait 5 seconds and check again.
                    console.log("Data is still processing, checking again in 5 seconds...");
                    setTimeout(fetchDetails, 5000);
                } else {
                    // Success! We got the real data.
                    console.log("Data received!", data);
                    setDetails(data);
                    setIsLoading(false); // Stop showing the "Loading..." message
                    setError('');
                }

            } catch (err) {
                if (!isCancelled) {
                    setError(err.message);
                    setIsLoading(false);
                }
            }
        };

        fetchDetails(); // This starts the first check

        // This is a cleanup function that runs if you navigate away from the page
        return () => {
            isCancelled = true;
        };
    }, [fileHash]); // This tells React to re-run the effect if the fileHash changes

    // Simple display for the demo
    const renderContent = () => {
        if (isLoading) {
            return <p>Loading extracted data...</p>;
        }
        if (error) {
            return <p style={{ color: 'red' }}>Error: {error}</p>;
        }
        if (details) {
            // The <pre> tag is great for showing formatted JSON for a demo
            return (
                <div>
                    <h3>Extracted Key-Value Pairs</h3>
                    <pre style={{ background: '#02040aff', padding: '1rem', borderRadius: '5px', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                        {JSON.stringify(details, null, 2)}
                    </pre>
                </div>
            );
        }
        return <p>No data to display.</p>;
    };

    return (
        <div className="main-chat" style={{ padding: '2rem' }}>
            <Link to="/dashboard">← Back to Dashboard</Link>
            {renderContent()}
        </div>
    );
}