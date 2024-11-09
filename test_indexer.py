from indexer import FileIndexer
import os

def test_pictures_indexing():
    # Set up the indexer with ChromaDB persistence directory
    persist_dir = "./chroma_db"
    indexer = FileIndexer(persist_dir)
    
    # Define the pictures directory
    pictures_dir = os.path.expanduser("~/Pictures")  # This expands to /Users/ecanton/Pictures
    
    # Define specific image extensions we want to index
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    
    print(f"Starting to index directory: {pictures_dir}")
    print(f"Looking for files with extensions: {', '.join(image_extensions)}")
    
    # Start indexing
    try:
        indexer.index_directories([pictures_dir], image_extensions)
        
        # Get and display indexed directories
        indexed_dirs = indexer.get_directories()
        print("\nIndexed directories:")
        for dir in indexed_dirs:
            print(f"- {dir}")
            
        # Get and display files in the Pictures directory
        files = indexer.get_files_in_directory(pictures_dir)
        print(f"\nIndexed files in {pictures_dir}:")
        for file in files:
            print(f"- {file['name']} ({file['type']})")
            
    except Exception as e:
        print(f"Error during indexing: {e}")

if __name__ == "__main__":
    test_pictures_indexing() 