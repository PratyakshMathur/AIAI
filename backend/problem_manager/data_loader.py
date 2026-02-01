"""
Load problem data from problems.db into DuckDB for session execution.
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "problems.db"

def load_problem_to_duckdb(problem_id: int, duckdb_conn):
    """
    Load all tables for a problem into DuckDB with aliased names.
    
    Tables are created as: tablename_problemid
    Example: customers_3, orders_3
    
    Args:
        problem_id: Problem ID to load
        duckdb_conn: DuckDB connection object
    """
    
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Problems database not found: {DB_PATH}")
    
    sqlite_conn = sqlite3.connect(DB_PATH)
    cursor = sqlite_conn.cursor()
    
    # Get all tables for this problem
    cursor.execute(
        "SELECT table_name, schema_json FROM problem_tables WHERE problem_id = ?",
        (problem_id,)
    )
    tables = cursor.fetchall()
    
    if not tables:
        print(f"⚠️  No tables found for problem {problem_id}")
        sqlite_conn.close()
        return
    
    loaded_tables = []
    
    for table_name, schema_json in tables:
        schema = json.loads(schema_json)
        
        # Create aliased table name
        aliased_name = f"{table_name}_{problem_id}"
        
        # Build CREATE TABLE statement
        columns = []
        for col in schema:
            col_name = col['name']
            col_type = col['type']
            columns.append(f"{col_name} {col_type}")
        
        create_sql = f"CREATE TABLE {aliased_name} ({', '.join(columns)})"
        
        try:
            duckdb_conn.execute(create_sql)
        except Exception as e:
            print(f"⚠️  Error creating table {aliased_name}: {e}")
            continue
        
        # Get all rows for this table
        cursor.execute(
            "SELECT row_json FROM table_data WHERE problem_id = ? AND table_name = ?",
            (problem_id, table_name)
        )
        rows = cursor.fetchall()
        
        # Insert rows
        if rows:
            placeholders = ', '.join(['?'] * len(schema))
            insert_sql = f"INSERT INTO {aliased_name} VALUES ({placeholders})"
            
            for (row_json,) in rows:
                row_data = json.loads(row_json)
                try:
                    duckdb_conn.execute(insert_sql, row_data)
                except Exception as e:
                    print(f"⚠️  Error inserting row into {aliased_name}: {e}")
        
        loaded_tables.append((table_name, aliased_name, len(rows)))
    
    sqlite_conn.close()
    
    print(f"✅ Loaded {len(loaded_tables)} tables for problem {problem_id}:")
    for original, aliased, row_count in loaded_tables:
        print(f"   {original} → {aliased} ({row_count} rows)")
    
    return loaded_tables

def get_problem_table_names(problem_id: int):
    """
    Get list of table names (without problem_id suffix) for a problem.
    Used for query validation.
    
    Returns: List of table names (e.g., ['customers', 'orders'])
    """
    if not DB_PATH.exists():
        return []
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT table_name FROM problem_tables WHERE problem_id = ?",
        (problem_id,)
    )
    tables = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    return tables
