import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "arena.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
        """
    )
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        users = [
            ("admin", "admin@zeroday.local", "supersecret123"),
            ("alice", "alice@zeroday.local", "hunter2"),
            ("bob", "bob@zeroday.local", "password"),
        ]
        cursor.executemany(
            "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
            users,
        )
    conn.commit()
    conn.close()


def fetch_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, password FROM users")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
