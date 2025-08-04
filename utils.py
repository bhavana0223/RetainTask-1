"""
Utility functions for user data validation and password management.
Provides secure validation and hashing utilities.
"""
import re
import bcrypt
import logging
from typing import Tuple, Optional
from config import get_config

logger = logging.getLogger(__name__)
config = get_config()

# Enhanced email regex pattern
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# Name validation pattern (allows letters, spaces, hyphens, apostrophes)
NAME_PATTERN = re.compile(r"^[a-zA-Z\s\-']{2,50}$")


def validate_user_data(name: str, email: str, password: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate user input data with enhanced security checks.
    
    Args:
        name: User's full name
        email: User's email address
        password: User's password (optional for updates)
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check for required fields
    if not name or not email:
        return False, "Name and email are required"
    
    # Validate name
    name = name.strip()
    if not name:
        return False, "Name cannot be empty or only whitespace"
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters long"
    
    if len(name) > 50:
        return False, "Name must be less than 50 characters"
    
    if not NAME_PATTERN.match(name):
        return False, "Name contains invalid characters"
    
    # Validate email
    email = email.strip().lower()
    if not email:
        return False, "Email cannot be empty or only whitespace"
    
    if len(email) > 254:  # RFC 5321 limit
        return False, "Email address is too long"
    
    if not EMAIL_PATTERN.match(email):
        return False, "Invalid email format"
    
    # Validate password if provided
    if password is not None:
        password_valid, password_error = validate_password(password)
        if not password_valid:
            return False, password_error
    
    return True, None


def validate_password(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password with enhanced security requirements.
    
    Args:
        password: The password to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < config.MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {config.MIN_PASSWORD_LENGTH} characters long"
    
    if len(password) > 128:  # Prevent DoS attacks with very long passwords
        return False, "Password must be less than 128 characters"
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, None


def sanitize_input(value: str, max_length: int = 255) -> str:
    """
    Sanitize input string by trimming and limiting length.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return ""
    
    # Strip whitespace and limit length
    sanitized = value.strip()[:max_length]
    return sanitized


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with appropriate cost factor.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    try:
        # Use cost factor of 12 for good security/performance balance
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to hash password: {e}")
        raise ValueError("Password hashing failed")


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password
        hashed: Hashed password from database
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logger.error(f"Failed to verify password: {e}")
        return False
