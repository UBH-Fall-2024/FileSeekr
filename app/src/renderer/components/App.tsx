// src/renderer/components/App.tsx
import React, { useState } from 'react';
import Navbar from './Navbar';
import Settings from './Settings';
import '../styles/main.css';

const App: React.FC = () => {
    const [currentPage, setCurrentPage] = useState<'main' | 'settings'>('main');
    const [message, setMessage] = useState<string>('');

    const toggleSettings = () => {
        setCurrentPage(currentPage === 'main' ? 'settings' : 'main');
    };

    return (
        <div className="container">
            <Navbar />
            {currentPage === 'main' ? (
                <>
                    <div className="main-content">
                        <h1>Electron + TypeScript + Flask</h1>
                        <p>Message from Flask: {message}</p>
                    </div>
                    <button className="floating-settings-button" onClick={toggleSettings}>
                        ⚙️
                    </button>
                </>
            ) : (
                <div>
                    <button className="back-button" onClick={toggleSettings}>
                        ← Back
                    </button>
                    <Settings />
                </div>
            )}
        </div>
    );
};

export default App;