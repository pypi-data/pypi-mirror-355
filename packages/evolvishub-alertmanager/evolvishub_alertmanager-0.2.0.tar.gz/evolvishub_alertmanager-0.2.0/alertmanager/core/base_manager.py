"""
Generic BaseManager class for database operations.
This class provides a reusable pattern for managing any type of data with SQLite.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from abc import ABC, abstractmethod

from .sqlite_adapter import SQLiteAdapter

logger = logging.getLogger(__name__)


class BaseManager(ABC):
    """
    Generic base manager class for database operations.
    
    This class provides common CRUD operations and can be extended
    for specific data types (alerts, users, products, etc.).
    """

    def __init__(self, db: SQLiteAdapter, table_name: str, migration_file: Optional[str] = None):
        """
        Initialize the BaseManager.

        Args:
            db (SQLiteAdapter): Database adapter instance
            table_name (str): Name of the database table to manage
            migration_file (str, optional): Path to SQL migration file for table creation
        """
        self.db = db
        self.table_name = table_name
        self.migration_file = migration_file
        self._ensure_table_exists()

    def _ensure_table_exists(self):
        """Ensure the table exists by executing the migration script if provided."""
        if not self.migration_file:
            logger.info(f"No migration file specified for table '{self.table_name}'")
            return

        try:
            migration_path = Path(self.migration_file)
            
            # If relative path, make it relative to project root
            if not migration_path.is_absolute():
                project_root = Path(__file__).parent.parent.parent
                migration_path = project_root / self.migration_file

            if migration_path.exists():
                with open(migration_path, 'r') as f:
                    sql = f.read()
                    self.db.execute_script(sql)
                logger.info(f"Table '{self.table_name}' created/verified successfully")
            else:
                logger.warning(f"Migration file not found: {migration_path}")
        except Exception as e:
            logger.error(f"Error creating table '{self.table_name}': {str(e)}")
            raise

    def create_record(self, data: Dict[str, Any], auto_timestamps: bool = True) -> int:
        """
        Create a new record with automatic timestamp handling.

        Args:
            data (Dict[str, Any]): Record data
            auto_timestamps (bool): Whether to automatically add created_at/updated_at timestamps

        Returns:
            int: ID of the created record
        """
        try:
            record_data = data.copy()
            
            # Add automatic timestamps if enabled
            if auto_timestamps:
                now = datetime.now()
                record_data.setdefault('created_at_evie', now)
                record_data.setdefault('updated_at_evie', now)

            # Handle JSON serialization for complex data types
            record_data = self._serialize_json_fields(record_data)

            last_id = self.db.insert_data(self.table_name, [record_data])
            logger.info(f"Record created in '{self.table_name}' table")
            return last_id

        except Exception as e:
            logger.error(f"Error creating record in '{self.table_name}': {str(e)}")
            raise

    def get_records(
        self,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get records with optional filtering and pagination.

        Args:
            filters (Dict[str, Any], optional): WHERE clause filters
            columns (List[str], optional): Columns to select. Defaults to all.
            order_by (str, optional): Column to order by
            limit (int, optional): Maximum number of records to return
            offset (int, optional): Number of records to skip

        Returns:
            List[Dict[str, Any]]: List of records
        """
        try:
            records = self.query_records(
                columns=columns,
                filters=filters,
                order_by=order_by,
                limit=limit,
                offset=offset
            )
            return records

        except Exception as e:
            logger.error(f"Error getting records from '{self.table_name}': {str(e)}")
            raise

    def get_record_by_id(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a single record by ID.
        
        Args:
            record_id (int): ID of the record to retrieve
            
        Returns:
            Dict[str, Any] or None: Record data or None if not found
        """
        try:
            records = self.query_records(filters={'id': record_id}, limit=1)
            return records[0] if records else None
        except Exception as e:
            logger.error(f"Error getting record {record_id} from '{self.table_name}': {str(e)}")
            return None

    def update_record(
        self, 
        record_id: int, 
        data: Dict[str, Any], 
        auto_timestamps: bool = True
    ) -> bool:
        """
        Update a record by ID.

        Args:
            record_id (int): ID of the record to update
            data (Dict[str, Any]): Data to update
            auto_timestamps (bool): Whether to automatically update updated_at timestamp

        Returns:
            bool: True if successful
        """
        try:
            update_data = data.copy()
            
            # Add automatic timestamp if enabled
            if auto_timestamps:
                update_data['updated_at_evie'] = datetime.now()

            # Handle JSON serialization
            update_data = self._serialize_json_fields(update_data)

            self.db.update_data(self.table_name, update_data, 'id = ?', (record_id,))
            logger.info(f"Record {record_id} updated in '{self.table_name}' table")
            return True

        except Exception as e:
            logger.error(f"Error updating record {record_id} in '{self.table_name}': {str(e)}")
            raise

    def delete_record(self, record_id: int) -> bool:
        """
        Delete a record by ID.

        Args:
            record_id (int): ID of the record to delete

        Returns:
            bool: True if successful
        """
        try:
            query = f"DELETE FROM {self.table_name} WHERE id = ?"
            self.db.execute_query(query, (record_id,))
            logger.info(f"Record {record_id} deleted from '{self.table_name}' table")
            return True

        except Exception as e:
            logger.error(f"Error deleting record {record_id} from '{self.table_name}': {str(e)}")
            raise

    def count_records(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count records with optional filtering.

        Args:
            filters (Dict[str, Any], optional): WHERE clause filters

        Returns:
            int: Number of records
        """
        try:
            query = f"SELECT COUNT(*) as count FROM {self.table_name}"
            params = []

            if filters:
                where_conditions = [f"{key} = ?" for key in filters.keys()]
                query += " WHERE " + " AND ".join(where_conditions)
                params.extend(filters.values())

            result = self.db.execute_query(query, params)
            return result[0]['count'] if result else 0

        except Exception as e:
            logger.error(f"Error counting records in '{self.table_name}': {str(e)}")
            raise

    def query_records(
        self,
        columns: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        custom_where: Optional[str] = None,
        custom_params: Optional[List[Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generic query function for the table with advanced filtering options.

        Args:
            columns (List[str], optional): Columns to select. Defaults to all.
            filters (Dict[str, Any], optional): Simple WHERE clause filters.
            order_by (str, optional): Column to order by.
            limit (int, optional): Limit number of results.
            offset (int, optional): Offset for results.
            custom_where (str, optional): Custom WHERE clause for complex queries.
            custom_params (List[Any], optional): Parameters for custom WHERE clause.

        Returns:
            List[Dict[str, Any]]: List of records.
        """
        try:
            # Build query components
            select_clause = ', '.join(columns) if columns else '*'
            query = f"SELECT {select_clause} FROM {self.table_name}"
            params = []

            # Add WHERE clause
            where_conditions = []

            # Simple filters
            if filters:
                where_conditions.extend([f"{key} = ?" for key in filters.keys()])
                params.extend(filters.values())

            # Custom WHERE clause
            if custom_where:
                where_conditions.append(custom_where)
                if custom_params:
                    params.extend(custom_params)

            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)

            # Add ORDER BY clause
            if order_by:
                query += f" ORDER BY {order_by}"

            # Add LIMIT and OFFSET
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
                if offset is not None:
                    query += " OFFSET ?"
                    params.append(offset)

            # Execute query and process results
            results = self.db.execute_query(query, params)

            # Deserialize JSON fields in results
            for i, record in enumerate(results):
                results[i] = self._deserialize_json_fields(record)

            return results

        except Exception as e:
            logger.error(f"Error in query_records for '{self.table_name}': {str(e)}")
            raise

    def delete_old_records(self, days: int = 30, date_column: str = 'created_at_evie') -> int:
        """
        Delete records older than specified days.

        Args:
            days (int): Number of days to keep records
            date_column (str): Column name containing the date to check

        Returns:
            int: Number of records deleted
        """
        try:
            query = f"DELETE FROM {self.table_name} WHERE {date_column} < datetime('now', ?)"
            self.db.execute_query(query, [f'-{days} days'])

            # Get the number of affected rows
            count_result = self.db.execute_query("SELECT changes() as count")
            deleted_count = count_result[0]['count'] if count_result else 0

            logger.info(f"Deleted {deleted_count} old records from '{self.table_name}' (older than {days} days)")
            return deleted_count

        except Exception as e:
            logger.error(f"Error deleting old records from '{self.table_name}': {str(e)}")
            raise

    def bulk_insert(self, records: List[Dict[str, Any]], auto_timestamps: bool = True) -> bool:
        """
        Insert multiple records in a single transaction.

        Args:
            records (List[Dict[str, Any]]): List of records to insert
            auto_timestamps (bool): Whether to automatically add timestamps

        Returns:
            bool: True if successful
        """
        if not records:
            return True

        try:
            processed_records = []
            for record in records:
                record_data = record.copy()

                # Add automatic timestamps if enabled
                if auto_timestamps:
                    now = datetime.now()
                    record_data.setdefault('created_at_evie', now)
                    record_data.setdefault('updated_at_evie', now)

                # Handle JSON serialization
                record_data = self._serialize_json_fields(record_data)
                processed_records.append(record_data)

            self.db.insert_data(self.table_name, processed_records)
            logger.info(f"Bulk inserted {len(processed_records)} records into '{self.table_name}' table")
            return True

        except Exception as e:
            logger.error(f"Error bulk inserting records into '{self.table_name}': {str(e)}")
            raise

    def _serialize_json_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Serialize dictionary/list fields to JSON strings.
        Override this method to specify which fields should be JSON serialized.

        Args:
            data (Dict[str, Any]): Record data

        Returns:
            Dict[str, Any]: Data with JSON fields serialized
        """
        result = data.copy()

        # Default behavior: serialize 'metadata' field if it exists and is not a string
        if 'metadata' in result and result['metadata'] is not None:
            if not isinstance(result['metadata'], str):
                result['metadata'] = json.dumps(result['metadata'])

        return result

    def _deserialize_json_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deserialize JSON string fields back to Python objects.
        Override this method to specify which fields should be JSON deserialized.

        Args:
            data (Dict[str, Any]): Record data

        Returns:
            Dict[str, Any]: Data with JSON fields deserialized
        """
        result = data.copy()

        # Default behavior: deserialize 'metadata' field if it exists and is a string
        if 'metadata' in result and result['metadata'] is not None:
            if isinstance(result['metadata'], str):
                try:
                    result['metadata'] = json.loads(result['metadata'])
                except (json.JSONDecodeError, TypeError):
                    # If JSON parsing fails, leave as string
                    pass

        return result

    @abstractmethod
    def get_schema_info(self) -> Dict[str, Any]:
        """
        Return schema information for this manager's table.
        This method should be implemented by subclasses to provide
        table-specific schema details.

        Returns:
            Dict[str, Any]: Schema information including columns, types, etc.
        """
        pass

    # Utility methods for common operations
    def exists(self, record_id: int) -> bool:
        """Check if a record exists by ID."""
        try:
            result = self.query_records(columns=['id'], filters={'id': record_id}, limit=1)
            return len(result) > 0
        except Exception:
            return False

    def get_latest_records(self, limit: int = 10, date_column: str = 'created_at_evie') -> List[Dict[str, Any]]:
        """Get the most recently created records."""
        return self.query_records(
            order_by=f'{date_column} DESC',
            limit=limit
        )

    def search_records(self, search_term: str, search_columns: List[str]) -> List[Dict[str, Any]]:
        """
        Search records across multiple columns.

        Args:
            search_term (str): Term to search for
            search_columns (List[str]): Columns to search in

        Returns:
            List[Dict[str, Any]]: Matching records
        """
        if not search_columns:
            return []

        try:
            # Build LIKE conditions for each column
            like_conditions = [f"{col} LIKE ?" for col in search_columns]
            custom_where = " OR ".join(like_conditions)

            # Parameters for LIKE queries (add % wildcards)
            search_params = [f"%{search_term}%" for _ in search_columns]

            return self.query_records(
                custom_where=custom_where,
                custom_params=search_params
            )

        except Exception as e:
            logger.error(f"Error searching records in '{self.table_name}': {str(e)}")
            raise
