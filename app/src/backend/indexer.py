import os
import pickle
import argparse
from pathlib import Path
from typing import List, Set, Optional
from embedding import get_embedding, get_text_embedding
import numpy as np
import chromadb
from chromadb import Client, Settings
from chromadb.utils import embedding_functions
from tqdm import tqdm
import concurrent.futures

class FileIndexer:
    def __init__(self, persist_directory: str):
        """
        Initialize the FileIndexer with ChromaDB persistence directory.
        
        Args:
            persist_directory (str): Directory to persist ChromaDB data
        """
        os.makedirs(persist_directory, exist_ok=True)
        self.persist_directory = persist_directory
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                allow_reset=True,
                is_persistent=True
            )
        )
        
        # Get or create collection - use a single collection name
        try:
            self.collection = self.client.get_collection("file_collection")
        except:
            self.collection = self.client.create_collection("file_collection")
        
        # Supported file extensions
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.text_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json'}
        
        # Load existing indexed files
        self.indexed_paths = self._load_indexed_paths()
        print(f"Connected to ChromaDB at {persist_directory} with {len(self.indexed_paths)} indexed files")

    def _load_indexed_paths(self) -> Set[str]:
        """Load already indexed paths from the collection"""
        try:
            results = self.collection.get()
            if results['metadatas']:
                return {meta['path'] for meta in results['metadatas']}
        except Exception as e:
            print(f"Warning: Error loading indexed paths: {e}")
        return set()

    def index_directories(self, directories: List[str], file_extensions: Optional[List[str]] = None):
        """
        Index new files in the specified directories.
        Skip files that are already indexed.
        """
        if file_extensions is None:
            file_extensions = list(self.image_extensions | self.text_extensions)

        # Collect only new files to process
        files_to_process = []
        for directory in directories:
            try:
                dir_path = Path(directory).expanduser().resolve()
                if not dir_path.exists():
                    print(f"Warning: Directory {directory} does not exist. Skipping...")
                    continue

                print(f"Scanning directory: {directory}")
                for file_path in dir_path.rglob('*'):
                    str_path = str(file_path)
                    if (file_path.is_file() and 
                        file_path.suffix.lower() in file_extensions and 
                        str_path not in self.indexed_paths):
                        files_to_process.append(file_path)
            except Exception as e:
                print(f"Error scanning directory {directory}: {e}")
                continue

        if not files_to_process:
            print("No new files to index.")
            return

        print(f"\nFound {len(files_to_process)} new files to index")
        
        # Process new files with progress bar
        with tqdm(total=len(files_to_process), desc="Indexing new files") as pbar:
            for file_path in files_to_process:
                try:
                    # Skip if already indexed
                    if str(file_path) in self.indexed_paths:
                        continue

                    # Get embedding using your custom embedding function
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
                    
                    # Add to indexed paths
                    self.indexed_paths.add(str(file_path))
                    
                except Exception as e:
                    print(f"\nFailed to process file: {file_path}. Error: {e}")
                
                pbar.update(1)

        print(f"\nIndexing complete. Total documents in collection: {self.collection.count()}")

    def remove_path(self, path: str):
        """Remove a path and all its files from the index"""
        try:
            # Get all documents that start with this path
            results = self.collection.get()
            if not results['metadatas']:
                return

            # Find IDs to remove
            ids_to_remove = []
            paths_to_remove = set()
            for i, metadata in enumerate(results['metadatas']):
                if metadata['path'].startswith(path):
                    ids_to_remove.append(results['ids'][i])
                    paths_to_remove.add(metadata['path'])

            if ids_to_remove:
                self.collection.delete(ids=ids_to_remove)
                # Update indexed paths
                self.indexed_paths -= paths_to_remove
                print(f"Removed {len(ids_to_remove)} files from index for path: {path}")
            
        except Exception as e:
            print(f"Error removing path {path}: {e}")

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

    def search(self, query: str, limit: int = 5) -> list:
        """
        Search for files matching the query using CLIP text embeddings.
        
        Args:
            query (str): The search term
            limit (int): Maximum number of results to return
        """
        try:
            # Get text embedding for the query
            query_embedding = get_text_embedding(query)
            
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=limit
            )
            
            formatted_results = []
            if results and len(results['documents'][0]) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    formatted_results.append({
                        'path': doc,
                        'name': Path(doc).name,
                        'similarity': results['distances'][0][i] if 'distances' in results else 0
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []

    def __del__(self):
        """Cleanup when the indexer is destroyed"""
        if hasattr(self, 'client'):
            try:
                self.client._system.close()
            except:
                pass

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