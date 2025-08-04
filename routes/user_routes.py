import logging
from flask import Blueprint, request, jsonify
from models import (
    get_all_users, get_user_by_id, create_user, update_user, delete_user,
    search_users_by_name, get_user_by_email
)
from utils import validate_user_data, hash_password, verify_password

user_routes = Blueprint('user_routes', __name__)

logger = logging.getLogger(__name__)

# Root health check route as per requirements
@user_routes.route('/', methods=['GET'])
def root_health_check():
    return jsonify({"status": "healthy"}), 200

@user_routes.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@user_routes.route('/users', methods=['GET'])
def fetch_all_users():
    try:
        users = get_all_users()
        return jsonify(users), 200
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return jsonify({"error": "Internal server error"}), 500

@user_routes.route('/user/<int:user_id>', methods=['GET'])
def fetch_user(user_id):
    try:
        user = get_user_by_id(user_id)
        if user:
            return jsonify(user), 200
        return jsonify({"error": "User not found"}), 404
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@user_routes.route('/users', methods=['POST'])
def create_new_user():
    if not request.is_json:
        return jsonify({"error": "Invalid or missing JSON"}), 400
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    valid, message = validate_user_data(name, email, password)
    if not valid:
        return jsonify({"error": message}), 400

    try:
        if get_user_by_email(email):
            return jsonify({"error": "Email already exists"}), 409

        password_hash = hash_password(password)
        user_id = create_user(name, email, password_hash)
        return jsonify({
            "message": "User created successfully",
            "user_id": user_id,
            "name": name,
            "email": email
        }), 201
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({"error": "Internal server error"}), 500

@user_routes.route('/user/<int:user_id>', methods=['PUT'])
def update_existing_user(user_id):
    if not request.is_json:
        return jsonify({"error": "Invalid or missing JSON"}), 400
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    valid, message = validate_user_data(name, email)
    if not valid:
        return jsonify({"error": message}), 400

    try:
        if not get_user_by_id(user_id):
            return jsonify({"error": "User not found"}), 404

        update_user(user_id, name, email)
        return jsonify({"message": "User updated successfully"}), 200
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@user_routes.route('/user/<int:user_id>', methods=['DELETE'])
def delete_existing_user(user_id):
    try:
        if not get_user_by_id(user_id):
            return jsonify({"error": "User not found"}), 404

        delete_user(user_id)
        return jsonify({"message": "User deleted successfully"}
                       ), 200
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@user_routes.route('/search', methods=['GET'])
def search_users():
    name = request.args.get('name')
    if not name:
        return jsonify({"error": "Please provide a name to search"}), 400
    try:
        users = search_users_by_name(name)
        return jsonify(users), 200
    except Exception as e:
        logger.error(f"Error searching users by name '{name}': {e}")
        return jsonify({"error": "Internal server error"}), 500

@user_routes.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"error": "Invalid or missing JSON"}), 400
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    try:
        user = get_user_by_email(email, include_password=True)
        if user and verify_password(password, user['password']):
            return jsonify({"status": "success", "user_id": user['id']}), 200
        return jsonify({"status": "failed", "error": "Invalid credentials"}), 401
    except Exception as e:
        logger.error(f"Error during login for email '{email}': {e}")
        return jsonify({"error": "Internal server error"}), 500