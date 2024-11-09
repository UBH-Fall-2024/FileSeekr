from flask import Flask, request, jsonify
from pathlib import Path
from pydantic import BaseModel
import numpy as np
import chromadb
from chromadb import Client, Settings
from typing import Optional
from embedding import get_embedding

class SearchResult(BaseModel):
    distance: float
    name: str
    path: str

class Result(BaseModel):
    similarity: float
    filename: str
    filetype: str
    size: int # in bytes
    thumbnail: Optional[str] # base64 encoded jpg thumbnail
    path: str # full path

class SearchResponse(BaseModel):
    results: list[Result]
    len: int

app = Flask(__name__)

# Load Chroma index and metadata
client = Client(Settings(
    persist_directory="./chroma_db",
    is_persistent=True
))
collection = client.get_or_create_collection("files")

class FileInfo(BaseModel):
    filename: str
    file_type: str
    file_size: int

def get_file_info(file_path: str) -> FileInfo:
    path = Path(file_path)
    
    if not path.is_file():
        raise FileNotFoundError(f"No file found at {file_path}")
    
    file_name = path.name
    file_extension = path.suffix
    file_size = path.stat().st_size
    
    return FileInfo(
        filename=file_name,
        file_type=file_extension,
        file_size=file_size
    )

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', default=None, type=str)
    
    if not query:
        return jsonify({"error": "Query parameter 'q' is required."}), 400
    
    try:
        # Get the embedding for the query
        query_embedding = get_embedding(query)
        
        # Search using Chroma
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=4
        )
        
        search_results = []
        for i, metadata in enumerate(results['metadatas'][0]):
            search_results.append({
                "similarity": float(results['distances'][0][i]),
                "filename": metadata['name'],
                "filetype": metadata['type'],
                "path": metadata['path'],
                "size": Path(metadata['path']).stat().st_size if Path(metadata['path']).exists() else 0,
                "thumbnail": None
            })

        return jsonify({"results": search_results, "len": len(search_results)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')