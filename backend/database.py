import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

DATABASE_FILE = BASE_DIR / "cloudnotes.db"


def get_db():

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():

    connection = get_db()

    cursor = connection.cursor()

    # Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Files table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            description TEXT,
            filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            uploaded_by TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            size REAL NOT NULL
        )
    """)

    # Create demo user
    cursor.execute(
        "SELECT id FROM users WHERE email = ?",
        ("admin@cloudnotes.com",)
    )

    user = cursor.fetchone()

    if user is None:

        cursor.execute("""
            INSERT INTO users
            (name, email, password)
            VALUES (?, ?, ?)
        """, (
            "Imad Khan",
            "admin@cloudnotes.com",
            "admin123"
        ))

    connection.commit()

    connection.close()