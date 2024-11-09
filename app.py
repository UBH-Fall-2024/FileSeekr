from flask import Flask, request, jsonify
from pathlib import Path
from pydantic import BaseModel
import numpy as np
import faiss
import pickle
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

# Load FAISS index and metadata
index = faiss.read_index("file_index.faiss")
with open("file_metadata.pkl", "rb") as f:
    file_metadata = pickle.load(f)

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
    
    # Get the embedding for the query
    query_embedding = get_embedding(query)

    # Perform the search using FAISS
    k = 4  # number of results to return
    distances, indices = index.search(query_embedding.reshape(1, -1), k)

    search_results = []
    for i, idx in enumerate(indices[0]):
        if idx != -1:  # FAISS uses -1 for empty slots
            search_results.append(SearchResult(
                distance=float(distances[0][i]),
                name=file_metadata[idx]['name'],
                path=file_metadata[idx]['path']
            ))

    ret = []
    for result in search_results:
        file_info = get_file_info(result.path)
        ret.append(Result(
            similarity=1 - (result.distance / 2),  # Convert distance to similarity
            filename=file_info.filename,
            filetype=file_info.file_type,
            size=file_info.file_size,
            path=result.path,
            thumbnail=None
        ))

    return jsonify(SearchResponse(results=ret, len=len(ret)).model_dump())

if __name__ == '__main__':
    app.run(debug=True)