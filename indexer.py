import os
import pickle
import argparse
from pathlib import Path
from typing import List
from embedding import get_embedding
import numpy as np
import chromadb
from chromadb import Client, Settings

class FileIndexer:
    def __init__(self, persist_directory: str):
        """
        Initialize the FileIndexer with ChromaDB persistence directory.
        
        Args:
            persist_directory (str): Directory to persist ChromaDB data
        """
        self.client = Client(Settings(
            persist_directory=persist_directory,
            is_persistent=True
        ))
        self.collection = self.client.get_or_create_collection("files")
        
        # Supported file extensions
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.text_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json'}
        
        print(f"Connected to ChromaDB collection with {self.collection.count()} documents")

    def index_directories(self, directories: List[str], file_extensions: List[str] = None):
        """
        Index all supported files in the specified directories.
        """
        if file_extensions is None:
            file_extensions = list(self.image_extensions | self.text_extensions)
            
        for directory in directories:
            dir_path = Path(directory).resolve()
            if not dir_path.exists():
                print(f"Warning: Directory {directory} does not exist. Skipping...")
                continue
                
            print(f"Indexing directory: {directory}")
            
            # Traverse the directory
            for file_path in dir_path.rglob('*'):
                if file_path.suffix.lower() not in file_extensions:
                    continue
                    
                if self._is_file_indexed(str(file_path)):
                    print(f"Skipping already indexed file: {file_path}")
                    continue
                    
                try:
                    # Get embedding based on file type
                    embedding = get_embedding(str(file_path))
                    
                    # Store file type in metadata
                    file_type = 'image' if file_path.suffix.lower() in self.image_extensions else 'text'
                    
                    # Add document to ChromaDB
                    self.collection.add(
                        embeddings=[embedding.tolist()],
                        documents=[str(file_path)],
                        metadatas=[{
                            'name': file_path.name,
                            'path': str(file_path),
                            'timestamp': file_path.stat().st_mtime,
                            'type': file_type
                        }],
                        ids=[str(file_path)]
                    )
                    
                    print(f"Successfully embedded and indexed: {file_path} ({file_type})")
                    
                except Exception as e:
                    print(f"Failed to process file: {file_path}. Error: {e}")

        print(f"Indexing complete. Total documents in collection: {self.collection.count()}")

    def _is_file_indexed(self, file_path: str) -> bool:
        """Check if a file is already indexed based on its path."""
        try:
            result = self.collection.get(ids=[str(file_path)])
            return len(result['ids']) > 0
        except:
            return False

    def get_directories(self):
        """Get a list of all indexed directories"""
        results = self.collection.get()
        if not results['metadatas']:
            return []
        
        # Extract unique directories from metadata
        directories = set()
        for metadata in results['metadatas']:
            directory = os.path.dirname(metadata['path'])
            directories.add(directory)
        
        return list(directories)

    def get_files_in_directory(self, directory):
        """Get all indexed files in a specific directory"""
        results = self.collection.get()
        if not results['metadatas']:
            return []
        
        files = []
        for metadata in results['metadatas']:
            if directory in metadata['path']:
                files.append({
                    'name': metadata['name'],
                    'type': metadata['type'],
                    'relative_path': os.path.relpath(metadata['path'], directory),
                    'path': metadata['path']
                })
        return files

def main():
    parser = argparse.ArgumentParser(description='Index files in specified directories')
    parser.add_argument('directories', nargs='+', help='Directories to index')
    parser.add_argument('--extensions', nargs='+', 
                      help='File extensions to index (default: all supported extensions)')
    parser.add_argument('--persist-directory', default='./chroma_db',
                      help='Directory to persist ChromaDB data')
    
    args = parser.parse_args()
    
    indexer = FileIndexer(args.persist_directory)
    indexer.index_directories(args.directories, args.extensions)

if __name__ == '__main__':
    main()