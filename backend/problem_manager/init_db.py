"""
Initialize the problems database with schema.
Run this once to create backend/problems.db
"""

import sqlite3
import os
from pathlib import Path

# Database path relative to backend/
DB_PATH = Path(__file__).parent.parent / "problems.db"

def init_problems_db():
    """Create problems.db with required schema"""
    
    # Remove existing database if present
    if DB_PATH.exists():
        print(f"⚠️  Removing existing database: {DB_PATH}")
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create problems table
    cursor.execute("""
        CREATE TABLE problems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            difficulty TEXT NOT NULL CHECK(difficulty IN ('easy', 'medium', 'hard')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create problem_tables table (stores schema for each table)
    cursor.execute("""
        CREATE TABLE problem_tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id INTEGER NOT NULL,
            table_name TEXT NOT NULL,
            schema_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE,
            UNIQUE(problem_id, table_name)
        )
    """)
    
    # Create table_data table (stores actual rows)
    cursor.execute("""
        CREATE TABLE table_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            problem_id INTEGER NOT NULL,
            table_name TEXT NOT NULL,
            row_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE
        )
    """)
    
    # Create index for faster lookups
    cursor.execute("CREATE INDEX idx_table_data_problem ON table_data(problem_id, table_name)")
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created problems database: {DB_PATH}")
    print("Schema created:")
    print("  - problems (id, title, description, difficulty)")
    print("  - problem_tables (id, problem_id, table_name, schema_json)")
    print("  - table_data (id, problem_id, table_name, row_json)")

if __name__ == "__main__":
    init_problems_db()
