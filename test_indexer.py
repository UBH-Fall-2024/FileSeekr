from indexer import FileIndexer
import argparse

def main():
    parser = argparse.ArgumentParser(description='Index and search files using CLIP embeddings')
    parser.add_argument('--dirs', nargs='+', required=True, help='Directories to index')
    parser.add_argument('--search', type=str, help='Search query (optional)')
    parser.add_argument('--db-path', default='./chroma_db', help='ChromaDB storage path')
    
    args = parser.parse_args()
    
    # Initialize indexer
    indexer = FileIndexer(args.db_path)
    
    # Index directories
    indexer.index_directories(args.dirs)
    
    # Perform search if query provided
    if args.search:
        print(f"\nSearching for: {args.search}")
        results = indexer.search(args.search)
        
        if results:
            print("\nSearch results:")
            for result in results:
                print(f"- {result['name']} (Similarity: {result['similarity']:.4f})")
        else:
            print("No results found")

if __name__ == "__main__":
    main() 