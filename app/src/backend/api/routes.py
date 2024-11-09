from flask import Blueprint, jsonify

api_bp = Blueprint('api', __name__)

@api_bp.route('/test')
def test():
    return jsonify({'message': 'Hello from Flask!'})