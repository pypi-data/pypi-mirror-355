"""
SQLite database adapter for generic database operations.
This is a standalone version that can be used independently.
"""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SQLiteAdapter:
    """SQLite database adapter for generic database operations."""
    
    def __init__(self, database_path: str, pool_size: int = 5, max_overflow: int = 10):
        """
        Initialize the SQLite adapter.
        
        Args:
            database_path (str): Path to the SQLite database file
            pool_size (int): Size of the connection pool (for compatibility)
            max_overflow (int): Maximum number of overflow connections (for compatibility)
        """
        self.database_path = database_path
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure the database file exists."""
        db_path = Path(self.database_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Test connection
        with self._get_connection() as conn:
            conn.execute("SELECT 1")
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection.
        
        Returns:
            sqlite3.Connection: Database connection
        """
        # For in-memory databases, we need to use the same connection
        if self.database_path == ":memory:":
            if not hasattr(self, '_memory_conn'):
                self._memory_conn = sqlite3.connect(self.database_path)
                self._memory_conn.row_factory = sqlite3.Row
            return self._memory_conn
        
        # For file-based databases, create a new connection
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute a query and return results.
        
        Args:
            query (str): SQL query
            params (tuple, optional): Query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(query, params or ())
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise
    
    def execute_script(self, sql: str):
        """
        Execute a SQL script.
        
        Args:
            sql (str): SQL script to execute
        """
        try:
            with self._get_connection() as conn:
                conn.executescript(sql)
                conn.commit()
        except Exception as e:
            logger.error(f"Error executing script: {str(e)}")
            raise
    
    def insert_data(self, table: str, data: List[Dict[str, Any]]) -> Optional[int]:
        """
        Insert data into a table.

        Args:
            table (str): Table name
            data (List[Dict[str, Any]]): Data to insert

        Returns:
            int: Last inserted row ID (for single row inserts)
        """
        if not data:
            return None

        try:
            with self._get_connection() as conn:
                columns = list(data[0].keys())
                placeholders = ', '.join(['?' for _ in columns])
                query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

                last_id = None
                for row in data:
                    values = [row[col] for col in columns]
                    cursor = conn.execute(query, values)
                    last_id = cursor.lastrowid

                conn.commit()
                return last_id
        except Exception as e:
            logger.error(f"Error inserting data: {str(e)}")
            raise
    
    def update_data(self, table: str, data: Dict[str, Any], where_clause: str, where_params: Tuple):
        """
        Update data in a table.
        
        Args:
            table (str): Table name
            data (Dict[str, Any]): Data to update
            where_clause (str): WHERE clause
            where_params (tuple): Parameters for WHERE clause
        """
        try:
            with self._get_connection() as conn:
                set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
                query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
                
                values = list(data.values()) + list(where_params)
                conn.execute(query, values)
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating data: {str(e)}")
            raise
    
    def get_last_row_id(self) -> int:
        """
        Get the ID of the last inserted row.
        
        Returns:
            int: Last inserted row ID
        """
        try:
            with self._get_connection() as conn:
                result = conn.execute("SELECT last_insert_rowid() as id").fetchone()
                return result['id'] if result else None
        except Exception as e:
            logger.error(f"Error getting last row ID: {str(e)}")
            raise
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists in the database.
        
        Args:
            table_name (str): Name of the table to check
            
        Returns:
            bool: True if table exists, False otherwise
        """
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_query(query, (table_name,))
            return len(result) > 0
        except Exception as e:
            logger.error(f"Error checking if table exists: {str(e)}")
            return False
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get information about table columns.
        
        Args:
            table_name (str): Name of the table
            
        Returns:
            List[Dict[str, Any]]: Column information
        """
        try:
            query = f"PRAGMA table_info({table_name})"
            return self.execute_query(query)
        except Exception as e:
            logger.error(f"Error getting table info: {str(e)}")
            raise
    
    def close(self):
        """Close the database connection (for in-memory databases)."""
        if hasattr(self, '_memory_conn'):
            self._memory_conn.close()
            delattr(self, '_memory_conn')
