"""
CLI tool for managing interview problems and their datasets.

Usage:
    python manage_problems.py add-problem --title "..." --description "..." --difficulty medium
    python manage_problems.py add-table --problem 1 --csv customers.csv
    python manage_problems.py list-problems
    python manage_problems.py view-problem 1
    python manage_problems.py delete-problem 1
"""

import argparse
import sqlite3
import json
import csv
import re
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "problems.db"

def get_db():
    """Get database connection"""
    if not DB_PATH.exists():
        print("❌ Database not found. Run init_db.py first:")
        print("   python backend/problem_manager/init_db.py")
        exit(1)
    return sqlite3.connect(DB_PATH)

def infer_column_type(value):
    """Infer SQL type from string value"""
    if not value or value.strip() == '':
        return 'TEXT'
    
    value = value.strip()
    
    # Check for INTEGER
    if re.match(r'^-?\d+$', value):
        return 'INTEGER'
    
    # Check for REAL (float)
    if re.match(r'^-?\d+\.\d+$', value):
        return 'REAL'
    
    # Check for DATE (YYYY-MM-DD)
    if re.match(r'^\d{4}-\d{2}-\d{2}$', value):
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return 'DATE'
        except:
            pass
    
    return 'TEXT'

def add_problem(title, description, difficulty):
    """Add a new problem"""
    if difficulty not in ['easy', 'medium', 'hard']:
        print(f"❌ Invalid difficulty: {difficulty}. Must be easy, medium, or hard.")
        return
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO problems (title, description, difficulty) VALUES (?, ?, ?)",
        (title, description, difficulty)
    )
    problem_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    print(f"✅ Created problem with ID: {problem_id}")
    print(f"   Title: {title}")
    print(f"   Difficulty: {difficulty}")

def add_table_from_csv(problem_id, csv_path):
    """Add a table to a problem from CSV file"""
    csv_path = Path(csv_path)
    
    if not csv_path.exists():
        print(f"❌ CSV file not found: {csv_path}")
        return
    
    # Derive table name from filename
    table_name = csv_path.stem.lower()
    
    # Read CSV
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        headers = next(reader)
        rows = list(reader)
    
    if not rows:
        print(f"❌ CSV file is empty: {csv_path}")
        return
    
    # Validate row count
    if len(rows) > 10000:
        print(f"❌ Dataset too large: {len(rows)} rows (max 10,000)")
        return
    
    # Infer schema from first few rows
    column_types = {}
    for col_idx, col_name in enumerate(headers):
        # Sample multiple rows to infer type
        sample_values = [row[col_idx] for row in rows[:min(10, len(rows))] if col_idx < len(row)]
        
        # Determine type by checking all samples
        inferred_type = 'TEXT'
        for val in sample_values:
            val_type = infer_column_type(val)
            if val_type == 'REAL':
                inferred_type = 'REAL'
            elif val_type == 'INTEGER' and inferred_type == 'TEXT':
                inferred_type = 'INTEGER'
            elif val_type == 'DATE' and inferred_type == 'TEXT':
                inferred_type = 'DATE'
        
        column_types[col_name] = inferred_type
    
    # Build schema JSON
    schema = [{"name": name, "type": column_types[name]} for name in headers]
    schema_json = json.dumps(schema)
    
    # Insert into database
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check problem exists
        cursor.execute("SELECT id FROM problems WHERE id = ?", (problem_id,))
        if not cursor.fetchone():
            print(f"❌ Problem ID {problem_id} not found")
            return
        
        # Insert table schema
        cursor.execute(
            "INSERT INTO problem_tables (problem_id, table_name, schema_json) VALUES (?, ?, ?)",
            (problem_id, table_name, schema_json)
        )
        
        # Insert rows
        for row in rows:
            # Validate column count
            if len(row) != len(headers):
                print(f"⚠️  Skipping malformed row: {row}")
                continue
            
            row_json = json.dumps(row)
            cursor.execute(
                "INSERT INTO table_data (problem_id, table_name, row_json) VALUES (?, ?, ?)",
                (problem_id, table_name, row_json)
            )
        
        conn.commit()
        print(f"✅ Added table '{table_name}' to problem {problem_id}")
        print(f"   Rows: {len(rows)}")
        columns_str = ', '.join([f"{s['name']} ({s['type']})" for s in schema])
        print(f"   Columns: {columns_str}")
        
    except sqlite3.IntegrityError as e:
        print(f"❌ Table '{table_name}' already exists for problem {problem_id}")
    finally:
        conn.close()

def list_problems():
    """List all problems"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, difficulty, created_at FROM problems ORDER BY id")
    problems = cursor.fetchall()
    
    if not problems:
        print("No problems found.")
        return
    
    print("\n📋 Problems:")
    print("-" * 80)
    for pid, title, difficulty, created_at in problems:
        # Count tables
        cursor.execute(
            "SELECT COUNT(DISTINCT table_name) FROM problem_tables WHERE problem_id = ?",
            (pid,)
        )
        table_count = cursor.fetchone()[0]
        
        print(f"ID: {pid} | {title}")
        print(f"  Difficulty: {difficulty} | Tables: {table_count} | Created: {created_at}")
        print()
    
    conn.close()

def view_problem(problem_id):
    """View problem details"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Get problem
    cursor.execute(
        "SELECT title, description, difficulty, created_at FROM problems WHERE id = ?",
        (problem_id,)
    )
    problem = cursor.fetchone()
    
    if not problem:
        print(f"❌ Problem ID {problem_id} not found")
        return
    
    title, description, difficulty, created_at = problem
    
    print(f"\n{'=' * 80}")
    print(f"Problem ID: {problem_id}")
    print(f"Title: {title}")
    print(f"Difficulty: {difficulty}")
    print(f"Created: {created_at}")
    print(f"{'=' * 80}\n")
    print("Description:")
    print(description)
    print()
    
    # Get tables
    cursor.execute(
        "SELECT table_name, schema_json FROM problem_tables WHERE problem_id = ? ORDER BY table_name",
        (problem_id,)
    )
    tables = cursor.fetchall()
    
    if tables:
        print(f"{'=' * 80}")
        print("Tables:")
        print()
        for table_name, schema_json in tables:
            schema = json.loads(schema_json)
            
            # Count rows
            cursor.execute(
                "SELECT COUNT(*) FROM table_data WHERE problem_id = ? AND table_name = ?",
                (problem_id, table_name)
            )
            row_count = cursor.fetchone()[0]
            
            print(f"  📊 {table_name} ({row_count} rows)")
            columns_str = ', '.join([f"{col['name']} ({col['type']})" for col in schema])
            print(f"     Columns: {columns_str}")
            print()
    else:
        print("No tables defined for this problem.")
    
    conn.close()

def delete_problem(problem_id):
    """Delete a problem and all associated data"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Check if exists
    cursor.execute("SELECT title FROM problems WHERE id = ?", (problem_id,))
    problem = cursor.fetchone()
    
    if not problem:
        print(f"❌ Problem ID {problem_id} not found")
        return
    
    title = problem[0]
    
    # Confirm deletion
    confirm = input(f"⚠️  Delete problem '{title}' (ID: {problem_id})? This will remove all tables and data. [y/N]: ")
    
    if confirm.lower() != 'y':
        print("Cancelled.")
        return
    
    # Delete (CASCADE will handle related tables)
    cursor.execute("DELETE FROM problems WHERE id = ?", (problem_id,))
    conn.commit()
    conn.close()
    
    print(f"✅ Deleted problem ID {problem_id}")

def main():
    parser = argparse.ArgumentParser(description="Manage interview problems")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # add-problem
    add_prob = subparsers.add_parser('add-problem', help='Add a new problem')
    add_prob.add_argument('--title', required=True, help='Problem title')
    add_prob.add_argument('--description', required=True, help='Problem description (markdown)')
    add_prob.add_argument('--difficulty', required=True, choices=['easy', 'medium', 'hard'])
    
    # add-table
    add_tbl = subparsers.add_parser('add-table', help='Add table from CSV')
    add_tbl.add_argument('--problem', type=int, required=True, help='Problem ID')
    add_tbl.add_argument('--csv', required=True, help='CSV file path')
    
    # list-problems
    subparsers.add_parser('list-problems', help='List all problems')
    
    # view-problem
    view_prob = subparsers.add_parser('view-problem', help='View problem details')
    view_prob.add_argument('problem_id', type=int, help='Problem ID')
    
    # delete-problem
    del_prob = subparsers.add_parser('delete-problem', help='Delete a problem')
    del_prob.add_argument('problem_id', type=int, help='Problem ID')
    
    args = parser.parse_args()
    
    if args.command == 'add-problem':
        add_problem(args.title, args.description, args.difficulty)
    elif args.command == 'add-table':
        add_table_from_csv(args.problem, args.csv)
    elif args.command == 'list-problems':
        list_problems()
    elif args.command == 'view-problem':
        view_problem(args.problem_id)
    elif args.command == 'delete-problem':
        delete_problem(args.problem_id)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
