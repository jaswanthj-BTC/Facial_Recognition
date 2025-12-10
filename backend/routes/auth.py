from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from backend.models.user import UserRepository
from backend.config import DatabaseConfig
import re

# Create Blueprint for authentication routes
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Get database instance
db = DatabaseConfig.get_db()
user_repo = UserRepository(db)


def validate_email(email):
    """Validate email format using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    Validate password strength
    At least 6 characters, contains letter and number
    """
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"

    if not any(char.isdigit() for char in password):
        return False, "Password must contain at least one number"

    if not any(char.isalpha() for char in password):
        return False, "Password must contain at least one letter"

    return True, "Valid"


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user

    Expected JSON:
    {
        "email": "user@example.com",
        "username": "username",
        "password": "password123"
    }

    Returns:
    {
        "success": true,
        "message": "User created successfully",
        "user_id": "..."
    }
    """
    try:
        # Get JSON data from request
        data = request.get_json()

        # Validate required fields
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400

        email = data.get('email', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        # Check if all fields are provided
        if not all([email, username, password]):
            return jsonify({
                'success': False,
                'message': 'Email, username, and password are required'
            }), 400

        # Validate email format
        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400

        # Validate username length
        if len(username) < 3:
            return jsonify({
                'success': False,
                'message': 'Username must be at least 3 characters long'
            }), 400

        # Validate password
        is_valid, msg = validate_password(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': msg
            }), 400

        # Create user in database
        success, message, user_id = user_repo.create_user(email, username, password)

        if success:
            return jsonify({
                'success': True,
                'message': message,
                'user_id': user_id
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Login user and return JWT token

    Expected JSON:
    {
        "email": "user@example.com",
        "password": "password123"
    }

    Returns:
    {
        "success": true,
        "message": "Login successful",
        "token": "jwt_token_here",
        "user": { ... }
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400

        email = data.get('email', '').strip()
        password = data.get('password', '')

        if not all([email, password]):
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400

        # Authenticate user
        success, message, user_data = user_repo.authenticate(email, password)

        if success:
            # Create JWT token
            access_token = create_access_token(identity=user_data['id'])

            return jsonify({
                'success': True,
                'message': message,
                'token': access_token,
                'user': user_data
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': message
            }), 401

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """
    Verify if JWT token is valid
    Protected route - requires valid JWT token in headers

    Headers:
    Authorization: Bearer <token>

    Returns:
    {
        "success": true,
        "user_id": "..."
    }
    """
    try:
        # Get user ID from JWT token
        current_user_id = get_jwt_identity()

        # Fetch user data
        user = user_repo.find_by_id(current_user_id)

        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        return jsonify({
            'success': True,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'username': user['username']
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get user profile information
    Protected route - requires valid JWT token

    Returns complete user profile with statistics
    """
    try:
        current_user_id = get_jwt_identity()
        user = user_repo.find_by_id(current_user_id)

        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        return jsonify({
            'success': True,
            'user': {
                'id': str(user['_id']),
                'email': user['email'],
                'username': user['username'],
                'created_at': user['created_at'].isoformat() if user.get('created_at') else None,
                'last_login': user['last_login'].isoformat() if user.get('last_login') else None,
                'detection_count': user.get('detection_count', 0)
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        }), 500