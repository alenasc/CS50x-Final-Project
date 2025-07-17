# db.py
"""
Database connection helper.
Provides a simple function to open a SQLite connection
with row factory configured for named columns.
"""

import sqlite3
import os

def get_db_connection():
    """
    Create and return a new SQLite connection to the database file.
    The row_factory is set to sqlite3.Row to allow access by column name.
    """
    # Build full path to database file in current directory
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn
