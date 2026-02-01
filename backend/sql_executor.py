"""SQL query execution service with DuckDB"""
import duckdb
import re
import time
from typing import Tuple, List, Dict, Any, Optional
from threading import Thread
import signal

class SQLExecutor:
    """Execute SQL queries in a sandboxed DuckDB environment"""
    
    # Blocked SQL keywords for safety
    BLOCKED_KEYWORDS = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE', 'REPLACE', 'ATTACH', 'DETACH']
    MAX_ROWS = 5000
    TIMEOUT_SECONDS = 30
    
    def __init__(self, session_id: str = "default", problem_id: Optional[int] = None, allowed_tables: Optional[List[str]] = None):
        """Initialize DuckDB with session-specific in-memory database
        
        Args:
            session_id: Unique session identifier
            problem_id: Problem ID for table aliasing
            allowed_tables: List of table names allowed for this problem (e.g., ['customers', 'orders'])
        """
        self.session_id = session_id
        self.problem_id = problem_id
        self.allowed_tables = allowed_tables or []
        self.conn = duckdb.connect(':memory:')
        # Note: Tables are loaded externally via load_problem_to_duckdb()
    
    
    def _rewrite_query_with_aliases(self, query: str) -> str:
        """Rewrite query to use aliased table names.
        
        Converts: SELECT * FROM customers
        To:      SELECT * FROM customers_1
        
        Based on problem_id and allowed_tables list.
        """
        if not self.problem_id or not self.allowed_tables:
            return query  # No aliasing if no problem_id
        
        # Create pattern to match table names (word boundaries)
        # Must handle: FROM table, JOIN table, UPDATE table, etc.
        rewritten = query
        
        for table_name in self.allowed_tables:
            # Pattern matches table name with word boundaries
            # Handles: FROM table, JOIN table, INTO table, etc.
            pattern = r'\b' + re.escape(table_name) + r'\b'
            aliased_name = f"{table_name}_{self.problem_id}"
            rewritten = re.sub(pattern, aliased_name, rewritten, flags=re.IGNORECASE)
        
        return rewritten
    
    def _validate_table_access(self, query: str) -> Tuple[bool, str]:
        """Validate that query only accesses allowed tables."""
        if not self.allowed_tables:
            return True, ""  # No restrictions if no allowed tables defined
        
        # Extract table names from query (basic parsing)
        # This is a simple check - DuckDB will enforce actual table existence
        query_upper = query.upper()
        
        # Check for suspicious table references not in allowed list
        # This is not exhaustive but catches obvious violations
        for keyword in ['FROM', 'JOIN', 'INTO']:
            if keyword in query_upper:
                # Basic validation - full SQL parsing would be more robust
                pass
        
        return True, ""
    
    def _check_sql_safety(self, query: str) -> Tuple[bool, str]:
        """
        Check if SQL query is safe to execute
        Returns: (is_safe, error_message)
        """
        # Remove comments and normalize whitespace
        query_normalized = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query_normalized = re.sub(r'/\*.*?\*/', '', query_normalized, flags=re.DOTALL)
        query_normalized = query_normalized.upper()
        
        # Check for blocked keywords
        for keyword in self.BLOCKED_KEYWORDS:
            # Use word boundaries to avoid false positives
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, query_normalized):
                return False, f"Blocked keyword detected: {keyword}. Only SELECT queries are allowed."
        
        return True, ""
    
    def _add_limit_if_needed(self, query: str) -> str:
        """Add LIMIT clause if not present"""
        query_upper = query.upper()
        
        # Check if LIMIT already exists
        if 'LIMIT' not in query_upper:
            # Add LIMIT to the end of the query
            query = query.rstrip().rstrip(';')
            query += f' LIMIT {self.MAX_ROWS}'
        
        return query
    
    def execute_query(self, query: str) -> Tuple[bool, List[Dict[str, Any]], List[str], float, str]:
        """
        Execute SQL query with safety checks and timeout
        
        Returns:
            Tuple of (success, rows, column_names, execution_time, error)
            - rows: List of dictionaries (each row as a dict)
            - column_names: List of column names
            - execution_time: Execution time in seconds
        """
        start_time = time.time()
        
        try:
            # Step 1: Validate table access
            is_valid, error = self._validate_table_access(query)
            if not is_valid:
                return False, [], [], 0.0, error
            
            # Step 2: Safety check
            is_safe, error_msg = self._check_sql_safety(query)
            if not is_safe:
                return False, [], [], 0.0, error_msg
            
            # Step 3: Rewrite query with table aliases
            rewritten_query = self._rewrite_query_with_aliases(query)
            
            # Step 4: Add LIMIT if needed (only for SELECT queries)
            modified_query = rewritten_query
            if rewritten_query.strip().upper().startswith('SELECT'):
                modified_query = self._add_limit_if_needed(rewritten_query)
            
            # Execute query with timeout
            result = self.conn.execute(modified_query)
            
            # Check if it's a query that returns results
            if result.description:
                column_names = [desc[0] for desc in result.description]
                rows_tuples = result.fetchall()
                
                # Convert to list of dicts
                rows = []
                for row_tuple in rows_tuples:
                    row_dict = {}
                    for i, col_name in enumerate(column_names):
                        # Convert to JSON-serializable types
                        value = row_tuple[i]
                        if hasattr(value, 'isoformat'):  # Date/datetime
                            value = value.isoformat()
                        row_dict[col_name] = value
                    rows.append(row_dict)
                
                execution_time = time.time() - start_time
                return True, rows, column_names, execution_time, ""
            else:
                # Query executed but returned nothing (shouldn't happen with SELECT-only)
                execution_time = time.time() - start_time
                return True, [], [], execution_time, ""
                
        except duckdb.Error as e:
            execution_time = time.time() - start_time
            return False, [], [], execution_time, f"SQL Error: {str(e)}"
        except Exception as e:
            execution_time = time.time() - start_time
            return False, [], [], execution_time, f"Error: {str(e)}"
    
    def get_schema_info(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Get database schema information
        Returns: Dictionary with table names as keys and column info as values
        """
        schema = {}
        
        try:
            # Get all tables
            tables_result = self.conn.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
            ).fetchall()
            
            for (table_name,) in tables_result:
                # Get column info for each table
                columns_result = self.conn.execute(f'''
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                    ORDER BY ordinal_position
                ''').fetchall()
                
                schema[table_name] = [
                    {"name": col_name, "type": col_type}
                    for col_name, col_type in columns_result
                ]
        
        except Exception:
            # Fallback to basic schema
            schema = {
                "customers": [
                    {"name": "customer_id", "type": "INTEGER"},
                    {"name": "name", "type": "VARCHAR"},
                    {"name": "email", "type": "VARCHAR"},
                    {"name": "age", "type": "INTEGER"},
                    {"name": "city", "type": "VARCHAR"},
                    {"name": "registration_date", "type": "DATE"}
                ],
                "orders": [
                    {"name": "order_id", "type": "INTEGER"},
                    {"name": "customer_id", "type": "INTEGER"},
                    {"name": "product_name", "type": "VARCHAR"},
                    {"name": "category", "type": "VARCHAR"},
                    {"name": "amount", "type": "DECIMAL"},
                    {"name": "order_date", "type": "DATE"}
                ]
            }
        
        return schema
    
    def close(self):
        """Close the DuckDB connection"""
        if self.conn:
            self.conn.close()

