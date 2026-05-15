import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "random.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS staff_directory (
            emp_id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_alias TEXT NOT NULL,
            emp_role TEXT NOT NULL,
            secret_passcode TEXT NOT NULL
        )
        """
    )
    cursor.execute("SELECT COUNT(*) FROM staff_directory")
    if cursor.fetchone()[0] == 0:
        staff = [
            ("admin", "System Administrator", "supersecret123"),
            ("alice", "HR Manager", "hunter2"),
            ("charlie", "Janitor", "password"),
        ]
        cursor.executemany(
            "INSERT INTO staff_directory (emp_alias, emp_role, secret_passcode) VALUES (?, ?, ?)",
            staff,
        )
    conn.commit()
    conn.close()

def fetch_all_staff():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT emp_id, emp_alias, emp_role, secret_passcode FROM staff_directory")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows
