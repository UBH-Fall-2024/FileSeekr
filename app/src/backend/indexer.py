from concurrent.futures import ThreadPoolExecutor, as_completed
from embedding import get_embedding, get_text_embedding
from pathlib import Path
from tqdm import tqdm
from typing import List, Set, Optional, Dict, Any
import chromadb
import numpy as np
import logging, multiprocessing, os, platform, subprocess

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
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection("file_collection")
        except:
            self.collection = self.client.create_collection("file_collection")
        
        # Supported file extensions
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        self.text_extensions = {'.txt', '.md', '.py', '.js', '.html', '.css', '.json'}
        self.pdf_extensions = {'.pdf'}
        
        # Load existing indexed files
        self.indexed_paths = self._load_indexed_paths()
        print(f"Connected to ChromaDB at {persist_directory} with {len(self.indexed_paths)} indexed files")

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(persist_directory, 'indexer.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

        # Set number of workers based on CPU cores
        self.max_workers = max(1, multiprocessing.cpu_count() - 1)
        self.batch_size = 128  # Increased batch size for better parallelization

    def _load_indexed_paths(self) -> Set[str]:
        try:
            results = self.collection.get()
            if results['metadatas']:
                return {meta['path'] for meta in results['metadatas']}
        except Exception as e:
            print(f"Warning: Error loading indexed paths: {e}")
        return set()

    def _process_files_parallel(self, files: List[Path]) -> List[Dict[str, Any]]:
        """
        Process multiple files in parallel using thread pools.
        """
        processed_items = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all files for processing
            future_to_file = {
                executor.submit(self._process_single_file, file_path): file_path 
                for file_path in files
            }
            
            # Process completed futures as they finish
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    if result is not None:
                        processed_items.append(result)
                except Exception as e:
                    self.logger.error(f"Error processing {file_path}: {e}")
        
        return processed_items

    def _process_single_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Process a single file and return its data.
        """
        try:
            embedding = get_embedding(str(file_path))
            if embedding is None:
                return None
                
            suffix = file_path.suffix.lower()
            file_type = 'image' if suffix in self.image_extensions else \
                       'pdf' if suffix in self.pdf_extensions else 'text'
            
            return {
                'embedding': embedding.tolist(),
                'document': str(file_path),
                'metadata': {
                    'name': file_path.name,
                    'path': str(file_path),
                    'timestamp': file_path.stat().st_mtime,
                    'type': file_type
                },
                'id': str(file_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            return None

    def index_directories(self, directories: List[str], file_extensions: Optional[List[str]] = None):
        """
        Index new files in the specified directories using parallel batch processing.
        """
        if file_extensions is None:
            file_extensions = list(self.image_extensions | self.text_extensions | self.pdf_extensions)

        # Collect files to process
        files_to_process = []
        for directory in directories:
            try:
                dir_path = Path(os.path.join(directory, '')).expanduser().resolve()
                if not dir_path.exists():
                    continue

                for file_path in dir_path.rglob('*'):
                    str_path = str(file_path)
                    if (file_path.is_file() and 
                        file_path.suffix.lower() in file_extensions and 
                        str_path not in self.indexed_paths):
                        files_to_process.append(file_path)

            except Exception as e:
                continue

        if not files_to_process:
            return

        total_files = len(files_to_process)
        self.logger.info(f"Found {total_files} new files to index")
        self.logger.info(f"Using {self.max_workers} worker threads")

        # Process files in parallel batches
        with tqdm(total=total_files, desc="Indexing files") as pbar:
            for i in range(0, total_files, self.batch_size):
                batch = files_to_process[i:i + self.batch_size]
                
                # Process the batch in parallel
                processed_items = self._process_files_parallel(batch)
                
                if processed_items:
                    try:
                        # Add batch to ChromaDB
                        self.collection.add(
                            embeddings=[item['embedding'] for item in processed_items],
                            documents=[item['document'] for item in processed_items],
                            metadatas=[item['metadata'] for item in processed_items],
                            ids=[item['id'] for item in processed_items]
                        )
                        
                        # Update indexed paths
                        self.indexed_paths.update(item['document'] for item in processed_items)
                        
                    except Exception as e:
                        self.logger.error(f"Error adding batch to collection: {e}")
                
                pbar.update(len(batch))

        self.logger.info(f"Indexing complete. Total documents in collection: {self.collection.count()}")

    def _add_to_collection(self, file_path: Path, embedding: np.ndarray):
        """Add a file and its embedding to the collection"""
        try:
            # Update file type detection to include PDFs
            suffix = file_path.suffix.lower()
            if suffix in self.image_extensions:
                file_type = 'image'
            elif suffix in self.pdf_extensions:
                file_type = 'pdf'
            else:
                file_type = 'text'
            
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
            self.logger.error(f"Failed to add {file_path} to collection: {e}")

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
        """
        try:
            # Debug logging
            self.logger.info(f"Searching for query: {query}")
            self.logger.info(f"Collection count: {self.collection.count()}")

            # Get text embedding for the query
            query_embedding = get_text_embedding(query)
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=min(limit, self.collection.count()),
                include=["metadatas", "distances", "documents"]
            )
            
            # Format results
            formatted_results = []
            if results and results['ids'] and len(results['ids'][0]) > 0:
                for i in range(len(results['ids'][0])):
                    metadata = results['metadatas'][0][i]
                    distance = float(results['distances'][0][i])
                    similarity = 1.0 - distance
                    
                    formatted_results.append({
                        'path': metadata['path'],
                        'name': metadata['name'],
                        'type': metadata['type'],
                        'similarity': round(similarity, 4)
                    })
                
                # Sort by similarity (highest first)
                formatted_results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            return []

    def open_file(self, file_path: str) -> bool:
        """
        Open a file using the default system application.
        
        Args:
            file_path (str): Path to the file to open
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"File not found: {file_path}")
                return False
                
            # Handle different operating systems
            system = platform.system()
            if system == 'Darwin':  # macOS
                subprocess.run(['open', file_path])
            elif system == 'Windows':
                os.startfile(file_path)
            else:  # Linux
                subprocess.run(['xdg-open', file_path])
                
            self.logger.info(f"Opened file: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error opening file {file_path}: {e}")
            return False

    def __del__(self):
        """Cleanup when the indexer is destroyed"""
        if hasattr(self, 'client'):
            try:
                self.client._system.close()
            except:
                pass
