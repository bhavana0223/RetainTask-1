"""
Database connection and initialization module.
Provides secure database connections and table creation.
"""
import sqlite3
import logging
import threading
from contextlib import contextmanager
from config import get_config

logger = logging.getLogger(__name__)
config = get_config()

# Thread-local storage for database connections
_local = threading.local()


def get_db_connection():
    """
    Get a database connection for the current thread.
    Uses thread-local storage to ensure thread safety.
    """
    if not hasattr(_local, 'connection') or _local.connection is None:
        try:
            _local.connection = sqlite3.connect(
                config.DATABASE_PATH,
                check_same_thread=True,  # Enforce thread safety
                timeout=30.0  # Add timeout to prevent deadlocks
            )
            _local.connection.row_factory = sqlite3.Row
            # Enable foreign keys for referential integrity
            _local.connection.execute("PRAGMA foreign_keys = ON")
            # Enable WAL mode for better concurrent access
            _local.connection.execute("PRAGMA journal_mode = WAL")
        except sqlite3.Error as e:
            logger.error(f"Failed to create database connection: {e}")
            raise
    
    return _local.connection


@contextmanager
def get_db_transaction():
    """
    Context manager for database transactions.
    Ensures proper commit/rollback behavior.
    """
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database transaction failed: {e}")
        raise
    finally:
        # Don't close the connection here as it's thread-local
        pass


def close_db_connection():
    """Close the database connection for the current thread."""
    if hasattr(_local, 'connection') and _local.connection is not None:
        _local.connection.close()
        _local.connection = None


def create_users_table():
    """
    Create the users table with proper constraints and indexes.
    """
    try:
        with get_db_transaction() as conn:
            # Create users table with enhanced constraints
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL CHECK(length(trim(name)) > 0),
                    email TEXT NOT NULL UNIQUE CHECK(length(trim(email)) > 0),
                    password TEXT NOT NULL CHECK(length(password) >= 60),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create index for faster email lookups
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
            ''')
            
            # Create trigger to update updated_at timestamp
            conn.execute('''
                CREATE TRIGGER IF NOT EXISTS update_users_timestamp 
                AFTER UPDATE ON users
                BEGIN
                    UPDATE users SET updated_at = CURRENT_TIMESTAMP 
                    WHERE id = NEW.id;
                END
            ''')
            
        logger.info("Database tables created/verified successfully")
        
    except sqlite3.Error as e:
        logger.error(f"Failed to create users table: {e}")
        raise
