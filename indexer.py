import os
import pickle
from pathlib import Path
from embedding import get_embedding
import numpy as np
import faiss

def index_files(root_dir: Path, index_path: str, metadata_path: str):
    """
    Traverse the root directory, extract embeddings for each file, and build a FAISS index.

    Args:
        root_dir (Path): The root directory to start indexing.
        index_path (str): Path to save the FAISS index.
        metadata_path (str): Path to save the file metadata.
    """
    # Initialize lists to store metadata and embeddings
    file_metadata = []
    embeddings = []

    # Traverse the directory structure
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            file_path = Path(dirpath) / filename
            try:
                # Obtain embedding for the file
                embedding = get_embedding(str(file_path))
                embeddings.append(embedding)

                # Store metadata
                metadata = {
                    'name': filename,
                    'path': str(file_path)
                }
                file_metadata.append(metadata)

            except Exception as e:
                print(f"Failed to index file: {file_path}. Error: {e}")

    if not embeddings:
        print("No embeddings found. Exiting indexing process.")
        return

    # Convert embeddings to a NumPy array
    embeddings_np = np.array(embeddings).astype('float32')

    # Initialize FAISS index
    dimension = embeddings_np.shape[1]
    index = faiss.IndexFlatL2(dimension)

    # Add embeddings to the index
    index.add(embeddings_np)
    print(f"FAISS index has been created with {index.ntotal} vectors.")

    # Save the FAISS index
    faiss.write_index(index, index_path)
    print(f"FAISS index saved to {index_path}")

    # Save the metadata
    with open(metadata_path, 'wb') as f:
        pickle.dump(file_metadata, f)
    print(f"File metadata saved to {metadata_path}")

if __name__ == '__main__':
    # Define paths
    root_directory = Path.home()  # User's home directory
    index_file = "file_index.faiss"
    metadata_file = "file_metadata.pkl"

    # Start indexing
    index_files(root_directory, index_file, metadata_file)