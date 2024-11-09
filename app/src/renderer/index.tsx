import React, { useState, useEffect } from 'react';
import ReactDOM from 'react-dom';
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

ReactDOM.render(<App />, document.getElementById('root'));