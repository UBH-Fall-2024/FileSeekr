// src/renderer/components/App.tsx
import React, { useState, useEffect } from 'react';
import Navbar from './Navbar';
import Settings from './Settings';
import '../styles/main.css';

const App: React.FC = () => {
    const [message, setMessage] = useState<string>('');
    const [error, setError] = useState<string>('');
    const [loading, setLoading] = useState<boolean>(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                // Updated port from 5000 to 5050
                const response = await fetch('http://localhost:3000/api/test');

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                setMessage(data.message);
                setError('');
            } catch (error) {
                console.error('Error:', error);
                setError('Failed to connect to Flask backend');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    return (
        <div className="container">
            <Navbar />
            <div className="content">
                <h1>Electron + TypeScript + Flask</h1>
                {loading && <p className="loading">Loading...</p>}
                {error && <p className="error">{error}</p>}
                {message && <p>Message from Flask: {message}</p>}
            </div>
            <Settings />
        </div>
    );
};



export default App;