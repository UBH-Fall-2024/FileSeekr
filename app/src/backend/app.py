from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Root route
@app.route('/')
def home():
    return jsonify({"message": "Flask backend is running"})

# Test API route
@app.route('/api/test')
def test():
    return jsonify({"message": "Hello from Flask!"})

# Error handling
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Not Found", "message": "The requested URL was not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal Server Error", "message": "An internal server error occurred"}), 500

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',  # localhost
        port=3000,         # Changed from 5000 to 5050
        debug=True
    )