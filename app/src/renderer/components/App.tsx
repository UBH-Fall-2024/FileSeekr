// src/renderer/components/App.tsx
import React, { useState } from 'react';
import Navbar from './Navbar';
import Settings from './Settings';
import '../styles/main.css';

const App: React.FC = () => {
    const [currentPage, setCurrentPage] = useState<'main' | 'settings'>('main');
    const [searchQuery, setSearchQuery] = useState<string>('');
    const [searchResults, setSearchResults] = useState<any[]>([]);

    const toggleSettings = () => {
        setCurrentPage(currentPage === 'main' ? 'settings' : 'main');
    };

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();

        console.log('Searching for:', searchQuery);
    };

    return (
        <div className="container">
            {currentPage === 'main' ? (
                <div className="main-page">
                    <div className="header">
                        <h1 className="title">AI-Powered File Similarity Finder</h1>
                        <button className="settings-button" onClick={toggleSettings}>
                            ⚙️
                        </button>
                    </div>

                    <div className="search-section">
                        <form onSubmit={handleSearch} className="search-form">
                            <input
                                type="text"
                                placeholder="Search for similar files..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="search-input"
                            />
                            <button type="submit" className="search-button">
                                Search
                            </button>
                        </form>
                    </div>

                    <div className="results-section">
                        <h2>Search Results</h2>
                        {searchResults.length === 0 ? (
                            <div className="no-results">
                                No results found. Try searching for something!
                            </div>
                        ) : (
                            <div className="results-list">
                                {/* Search results would go here */}
                            </div>
                        )}
                    </div>
                </div>
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