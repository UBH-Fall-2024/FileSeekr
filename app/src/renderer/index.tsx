import React, { useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const App: React.FC = () => {
    const [message, setMessage] = useState<string>('');

    useEffect(() => {
        // Test Flask backend connection
        fetch('http://localhost:5000/api/test')
            .then(response => response.json())
            .then(data => setMessage(data.message))
            .catch(error => console.error('Error:', error));
    }, []);

    return (
        <div>
            <h1>Electron + TypeScript + Flask</h1>
            <p>Message from Flask: {message}</p>
        </div>
    );
};

// Get the root element
const container = document.getElementById('root');

// Make sure container exists before creating root
if (!container) {
    throw new Error('Failed to find the root element');
}

// Create a root
const root = createRoot(container);

// Initial render
root.render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);