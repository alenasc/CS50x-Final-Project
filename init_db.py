# init_db.py
"""
Database initialization script.
Reads schema.sql and applies it to reset or create the database.
"""
import sqlite3
import os

# Path to the database file
db_path = os.path.join(os.path.dirname(__file__), "database.db")

# Open a connection, apply schema, and close
with open("schema.sql", "r") as f:
    schema = f.read()

conn = sqlite3.connect(db_path)
conn.executescript(schema)
conn.close()

print("✅ Database initialized with schema.")
