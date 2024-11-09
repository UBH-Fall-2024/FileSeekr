// src/renderer/components/App.tsx
import React, { useState } from 'react';
import Navbar from './Navbar';
import Settings from './Settings';
import '../styles/main.css';
import axios from 'axios';

interface SearchResult {
    similarity: number;
    filename: string;
    filetype: string;
    size: number;
    thumbnail?: string;
    path: string;
}

const App: React.FC = () => {
    const [currentPage, setCurrentPage] = useState<'main' | 'settings'>('main');
    const [searchQuery, setSearchQuery] = useState<string>('');
    const [searchResults, setSearchResults] = useState<SearchResult[]>([]);

    const toggleSettings = () => {
        setCurrentPage(currentPage === 'main' ? 'settings' : 'main');
    };

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        
        try {
            const response = await axios.get(`http://localhost:5001/search?q=${encodeURIComponent(searchQuery)}`);
            setSearchResults(response.data.results);
        } catch (error) {
            console.error('Search failed:', error);
            setSearchResults([]); // Clear results on error
        }
    };

    return (
        <div className="container">
            {currentPage === 'main' ? (
                <div className="main-page">
                    <div className="header">
                        <h1 className="title">FileSeekr: AI-Powered File Similarity Finder</h1>
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
                                {searchResults.map((result: SearchResult, index) => (
                                    <div key={index} className="result-item">
                                        <h3>{result.filename}</h3>
                                        <p>Type: {result.filetype}</p>
                                        <p>Similarity: {(1 - result.similarity).toFixed(2)}</p>
                                        <p>Size: {(result.size / 1024).toFixed(2)} KB</p>
                                        <p>Path: {result.path}</p>
                                    </div>
                                ))}
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