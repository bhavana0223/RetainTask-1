"""
User data model layer.
Provides secure database operations for user management.
"""
import logging
from typing import List, Dict, Optional, Any
from sqlite3 import Error, IntegrityError
from db import get_db_transaction, get_db_connection
from utils import sanitize_input

logger = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    """Raised when a user is not found."""
    pass


class UserAlreadyExistsError(Exception):
    """Raised when trying to create a user that already exists."""
    pass


def get_all_users() -> List[Dict[str, Any]]:
    """
    Retrieve all users from the database.
    
    Returns:
        List of user dictionaries (without passwords)
    
    Raises:
        Exception: If database operation fails
    """
    try:
        with get_db_transaction() as conn:
            users = conn.execute(
                "SELECT id, name, email, created_at, updated_at FROM users ORDER BY id"
            ).fetchall()
            return [dict(user) for user in users]
    except Error as e:
        logger.error(f"Database error in get_all_users: {e}")
        raise Exception("Failed to retrieve users") from e


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user by their ID.
    
    Args:
        user_id: The user's ID
    
    Returns:
        User dictionary (without password) or None if not found
    
    Raises:
        Exception: If database operation fails
        ValueError: If user_id is invalid
    """
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("User ID must be a positive integer")
    
    try:
        with get_db_transaction() as conn:
            user = conn.execute(
                "SELECT id, name, email, created_at, updated_at FROM users WHERE id = ?",
                (user_id,)
            ).fetchone()
            return dict(user) if user else None
    except Error as e:
        logger.error(f"Database error in get_user_by_id for user_id {user_id}: {e}")
        raise Exception("Failed to retrieve user") from e


def get_user_by_email(email: str, include_password: bool = False) -> Optional[Dict[str, Any]]:
    """
    Retrieve a user by their email address.
    
    Args:
        email: The user's email address
        include_password: Whether to include password hash in result
    
    Returns:
        User dictionary or None if not found
    
    Raises:
        Exception: If database operation fails
        ValueError: If email is invalid
    """
    if not email or not isinstance(email, str):
        raise ValueError("Email must be a non-empty string")
    
    email = sanitize_input(email.lower())
    
    try:
        with get_db_transaction() as conn:
            if include_password:
                query = "SELECT * FROM users WHERE email = ?"
            else:
                query = "SELECT id, name, email, created_at, updated_at FROM users WHERE email = ?"
            
            user = conn.execute(query, (email,)).fetchone()
            return dict(user) if user else None
    except Error as e:
        logger.error(f"Database error in get_user_by_email for email {email}: {e}")
        raise Exception("Failed to retrieve user") from e


def create_user(name: str, email: str, password_hash: str) -> int:
    """
    Create a new user in the database.
    
    Args:
        name: User's full name
        email: User's email address
        password_hash: Hashed password
    
    Returns:
        The ID of the newly created user
    
    Raises:
        UserAlreadyExistsError: If email already exists
        Exception: If database operation fails
        ValueError: If input parameters are invalid
    """
    if not all([name, email, password_hash]):
        raise ValueError("Name, email, and password_hash are required")
    
    # Sanitize inputs
    name = sanitize_input(name, 50)
    email = sanitize_input(email.lower(), 254)
    
    try:
        with get_db_transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )
            user_id = cursor.lastrowid
            
            logger.info(f"Created user with ID {user_id} and email {email}")
            return user_id
            
    except IntegrityError as e:
        if "email" in str(e).lower():
            logger.warning(f"Attempt to create user with existing email: {email}")
            raise UserAlreadyExistsError("Email already exists") from e
        else:
            logger.error(f"Integrity error in create_user: {e}")
            raise Exception("Failed to create user due to data constraint") from e
    except Error as e:
        logger.error(f"Database error in create_user: {e}")
        raise Exception("Failed to create user") from e


def update_user(user_id: int, name: str, email: str) -> None:
    """
    Update an existing user's information.
    
    Args:
        user_id: The user's ID
        name: New name
        email: New email address
    
    Raises:
        UserNotFoundError: If user doesn't exist
        UserAlreadyExistsError: If email already exists for another user
        Exception: If database operation fails
        ValueError: If input parameters are invalid
    """
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("User ID must be a positive integer")
    
    if not all([name, email]):
        raise ValueError("Name and email are required")
    
    # Sanitize inputs
    name = sanitize_input(name, 50)
    email = sanitize_input(email.lower(), 254)
    
    try:
        with get_db_transaction() as conn:
            # Check if user exists
            existing_user = conn.execute(
                "SELECT id FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            
            if not existing_user:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            # Check if email is already taken by another user
            email_check = conn.execute(
                "SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id)
            ).fetchone()
            
            if email_check:
                raise UserAlreadyExistsError("Email already exists for another user")
            
            # Update the user
            conn.execute(
                "UPDATE users SET name = ?, email = ? WHERE id = ?",
                (name, email, user_id)
            )
            
            logger.info(f"Updated user {user_id}")
            
    except (UserNotFoundError, UserAlreadyExistsError):
        raise
    except Error as e:
        logger.error(f"Database error in update_user for user_id {user_id}: {e}")
        raise Exception("Failed to update user") from e


def delete_user(user_id: int) -> None:
    """
    Delete a user from the database.
    
    Args:
        user_id: The user's ID
    
    Raises:
        UserNotFoundError: If user doesn't exist
        Exception: If database operation fails
        ValueError: If user_id is invalid
    """
    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("User ID must be a positive integer")
    
    try:
        with get_db_transaction() as conn:
            # Check if user exists first
            existing_user = conn.execute(
                "SELECT id FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            
            if not existing_user:
                raise UserNotFoundError(f"User with ID {user_id} not found")
            
            # Delete the user
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
            
            logger.info(f"Deleted user {user_id}")
            
    except UserNotFoundError:
        raise
    except Error as e:
        logger.error(f"Database error in delete_user for user_id {user_id}: {e}")
        raise Exception("Failed to delete user") from e


def search_users_by_name(name: str) -> List[Dict[str, Any]]:
    """
    Search for users by name using LIKE pattern matching.
    
    Args:
        name: Name pattern to search for
    
    Returns:
        List of matching user dictionaries (without passwords)
    
    Raises:
        Exception: If database operation fails
        ValueError: If name is invalid
    """
    if not name or not isinstance(name, str):
        raise ValueError("Name must be a non-empty string")
    
    name = sanitize_input(name, 50)
    search_pattern = f'%{name}%'
    
    try:
        with get_db_transaction() as conn:
            users = conn.execute(
                "SELECT id, name, email, created_at, updated_at FROM users WHERE name LIKE ? ORDER BY name",
                (search_pattern,)
            ).fetchall()
            return [dict(user) for user in users]
    except Error as e:
        logger.error(f"Database error in search_users_by_name for name '{name}': {e}")
        raise Exception("Failed to search users") from e