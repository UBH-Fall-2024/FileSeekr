from flask import Flask, request, jsonify
from flask_cors import CORS
from indexer import FileIndexer
from PIL import Image
import atexit, base64, fitz, io, logging, mimetypes, os, signal, sys

app = Flask(__name__)
CORS(app)

# Add logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize ChromaDB client and collection
current_dir = os.path.dirname(os.path.abspath(__file__))
chroma_db_path = os.path.join(current_dir, '..', '..', '..', 'chroma_db')
os.makedirs(chroma_db_path, exist_ok=True)

# Initialize the indexer
indexer = FileIndexer(chroma_db_path)

def cleanup():
    try:
        logger.info("Cleaning up Flask server...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Cleanup error: {e}")

# Register cleanup handlers
atexit.register(cleanup)
signal.signal(signal.SIGINT, lambda s, f: cleanup())

def get_thumbnail(file_path, max_size=(100, 100)):
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            with Image.open(file_path) as img:
                img.thumbnail(max_size)
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                encoded = base64.b64encode(buffer.getvalue()).decode()
                return f"data:image/png;base64,{encoded}"
        elif ext == '.pdf':
            try:
                doc = fitz.open(file_path)
                if doc.page_count > 0:
                    page = doc[0]
                    pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
                    img_data = pix.tobytes()
                    img = Image.frombytes("RGB", [pix.width, pix.height], img_data)
                    img.thumbnail(max_size)
                    buffer = io.BytesIO()
                    img.save(buffer, format='PNG')
                    encoded = base64.b64encode(buffer.getvalue()).decode()
                    return f"data:image/png;base64,{encoded}"
            except Exception as e:
                print(f"PDF thumbnail generation error: {e}")
                return "pdf-file-icon"
        else:
            # Return file type icon based on extension
            if ext in ['.txt', '.md']:
                return "text-file-icon"
            elif ext in ['.py', '.js', '.html', '.css']:
                return "code-file-icon"
            elif ext == '.pdf':
                return "pdf-file-icon"
            else:
                return "generic-file-icon"
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        return None

@app.route('/api/settings/paths', methods=['POST'])
def update_paths():
    data = request.json
    paths = data.get('paths', [])
    file_types = data.get('fileTypes', {})
    
    # Expand user paths and ensure trailing slash
    expanded_paths = [os.path.join(os.path.expanduser(path), '') for path in paths]
    
    # Convert file types to extensions
    extensions = []
    if file_types.get('documents'):
        extensions.extend(['.txt'])
    if file_types.get('images'):
        extensions.extend(['.jpg', '.jpeg', '.png'])
    if file_types.get('pdfs'):
        extensions.extend(['.pdf'])

    try:
        # Index new paths (existing files will be skipped)
        indexer.index_directories(expanded_paths, extensions)
        return jsonify({'success': True, 'message': 'Paths indexed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/')
def home():
    return "FileSeekr API is running!"

@app.route('/open-file', methods=['POST'])
def open_file_endpoint():
    try:
        data = request.json
        file_path = data.get('path')
        
        if not file_path:
            return jsonify({'success': False, 'error': 'No file path provided'}), 400
            
        success = indexer.open_file(file_path)
        return jsonify({'success': success})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/search', methods=['GET'])
def search():
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({'results': []})
        
        # Get number of results to return (default 5)
        limit = request.args.get('limit', 5, type=int)
        
        # Perform search using indexer
        results = indexer.search(query, limit)
        
        # Format results
        formatted_results = []
        for result in results:
            try:
                file_path = result['path']
                file_stats = os.stat(file_path)
                
                # Update filetype detection to properly handle PDFs
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                    filetype = 'image'
                elif ext == '.pdf':
                    filetype = 'pdf'
                else:
                    filetype = 'document'
                
                formatted_results.append({
                    'filename': os.path.basename(file_path),
                    'filetype': filetype,
                    'similarity': result['similarity'],
                    'size': file_stats.st_size,
                    'path': file_path,
                    'thumbnail': get_thumbnail(file_path)
                })
            except (OSError, KeyError) as e:
                print(f"Error processing result {result}: {e}")
                continue
                
        return jsonify({'results': formatted_results})
        
    except Exception as e:
        print(f"Search error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Update the main block
if __name__ == '__main__':
    try:
        logger.info("Starting Flask server...")
        # Print ready message that Electron can detect
        print("FLASK_SERVER_READY")
        sys.stdout.flush()
        app.run(host='127.0.0.1', port=5001, debug=False)
    except Exception as e:
        logger.error(f"Flask server error: {e}")
        sys.exit(1)
