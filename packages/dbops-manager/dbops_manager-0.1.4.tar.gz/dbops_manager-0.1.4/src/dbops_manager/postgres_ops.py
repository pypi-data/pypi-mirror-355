"""Core PostgreSQL operations module."""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool

from .exceptions import ConnectionError, QueryError
from .config_loader import load_from_env, validate_config

# Configure logging
logger = logging.getLogger(__name__)

class PostgresOps:
    """A lightweight PostgreSQL operations manager."""
    
    def __init__(self, config: Dict[str, str], logging_enabled: bool = False, max_pool_size: int = 32):
        """
        Initialize PostgreSQL operations manager.
        
        Args:
            config: PostgreSQL configuration dictionary
            logging_enabled: Enable logging for database operations
            max_pool_size: Maximum number of connections in the pool
        """
        self.logging_enabled = logging_enabled
        if self.logging_enabled:
            logger.info("Initializing PostgreSQL operations")
        
        validate_config(config, logging_enabled)
        self.config = config
        self._pool = None
        self._max_pool_size = max_pool_size
        self._local = threading.local()
        
        # Initialize connection pool
        self._init_connection_pool()
        
        # Create logs table if logging is enabled
        if self.logging_enabled:
            self._create_logs_table()
    
    def _init_connection_pool(self):
        """Initialize the connection pool."""
        try:
            self._pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=self._max_pool_size,
                **self.config
            )
        except psycopg2.Error as e:
            error_msg = f"Failed to initialize connection pool: {str(e)}"
            if self.logging_enabled:
                logger.error(error_msg)
            raise ConnectionError(error_msg)
    
    def _create_logs_table(self):
        """Create the logs table if it doesn't exist."""
        create_logs_table_sql = """
        CREATE TABLE IF NOT EXISTS dbops_manager_logs (
            id SERIAL PRIMARY KEY,
            query TEXT NOT NULL,
            params TEXT,
            execution_time DOUBLE PRECISION NOT NULL,
            rows_affected INTEGER,
            status VARCHAR(20) NOT NULL,
            error_message TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
        """
        self.execute(create_logs_table_sql)
    
    def _log_operation(self, query: str, params: Optional[List[Any]], execution_time: float,
                      rows_affected: int, status: str, error_message: Optional[str] = None):
        """Log database operation to the logs table."""
        if not self.logging_enabled:
            return
        
        log_sql = """
        INSERT INTO dbops_manager_logs (query, params, execution_time, rows_affected, status, error_message)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        try:
            self.execute(log_sql, [
                query,
                str(params) if params else None,
                execution_time,
                rows_affected,
                status,
                error_message
            ])
        except Exception as e:
            logger.error(f"Failed to log operation: {str(e)}")
    
    def _get_connection(self):
        """Get a connection from the pool."""
        try:
            if not hasattr(self._local, 'conn') or self._local.conn.closed:
                self._local.conn = self._pool.getconn()
            return self._local.conn
        except psycopg2.Error as e:
            error_msg = f"Failed to get connection from pool: {str(e)}"
            if self.logging_enabled:
                logger.error(error_msg)
            raise ConnectionError(error_msg)
    
    def _release_connection(self, conn):
        """Release a connection back to the pool."""
        if conn and not conn.closed:
            self._pool.putconn(conn)
    
    @classmethod
    def from_env(cls, env_prefix: str = "DB_", logging_enabled: bool = False,
                max_pool_size: int = 32) -> 'PostgresOps':
        """Create instance from environment variables."""
        config = load_from_env(env_prefix, logging_enabled)
        return cls(config, logging_enabled, max_pool_size)
    
    @classmethod
    def from_config(cls, config: Dict[str, str], logging_enabled: bool = False,
                   max_pool_size: int = 32) -> 'PostgresOps':
        """Create instance from configuration dictionary."""
        return cls(config, logging_enabled, max_pool_size)
    
    def fetch(
        self,
        query: str,
        params: Optional[List[Any]] = None,
        as_dict: bool = True
    ) -> List[Union[Dict[str, Any], Tuple]]:
        """
        Execute a SELECT query and fetch all results.
        
        Args:
            query: SQL query string
            params: Query parameters for parameterized queries
            as_dict: Return results as dictionaries (default: True)
        
        Returns:
            List of query results
        
        Raises:
            QueryError: If query execution fails
        """
        if self.logging_enabled:
            logger.info("Executing fetch query")
            logger.debug("Query: %s, Params: %s", query, params)
        
        start_time = datetime.now()
        conn = self._get_connection()
        cursor_factory = RealDictCursor if as_dict else None
        
        try:
            with conn.cursor(cursor_factory=cursor_factory) as cur:
                cur.execute(query, params)
                results = cur.fetchall()
                
                execution_time = (datetime.now() - start_time).total_seconds()
                self._log_operation(query, params, execution_time, len(results), "SUCCESS")
                
                if self.logging_enabled:
                    logger.info("Query executed successfully")
                    logger.debug("Results: %s", results)
                
                return results
        except psycopg2.Error as e:
            error_msg = f"Query execution failed: {str(e)}"
            execution_time = (datetime.now() - start_time).total_seconds()
            self._log_operation(query, params, execution_time, 0, "ERROR", str(e))
            
            if self.logging_enabled:
                logger.error(error_msg)
            conn.rollback()
            raise QueryError(error_msg)
    
    def execute(
        self,
        query: str,
        params: Optional[List[Any]] = None
    ) -> int:
        """
        Execute a modification query (INSERT, UPDATE, DELETE).
        
        Args:
            query: SQL query string
            params: Query parameters for parameterized queries
        
        Returns:
            Number of affected rows
        
        Raises:
            QueryError: If query execution fails
        """
        if self.logging_enabled:
            logger.info("Executing modification query")
            logger.debug("Query: %s, Params: %s", query, params)
        
        start_time = datetime.now()
        conn = self._get_connection()
        
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                conn.commit()
                affected_rows = cur.rowcount
                
                execution_time = (datetime.now() - start_time).total_seconds()
                self._log_operation(query, params, execution_time, affected_rows, "SUCCESS")
                
                if self.logging_enabled:
                    logger.info("Query executed successfully")
                    logger.debug("Affected rows: %d", affected_rows)
                
                return affected_rows
        except psycopg2.Error as e:
            error_msg = f"Query execution failed: {str(e)}"
            execution_time = (datetime.now() - start_time).total_seconds()
            self._log_operation(query, params, execution_time, 0, "ERROR", str(e))
            
            if self.logging_enabled:
                logger.error(error_msg)
            conn.rollback()
            raise QueryError(error_msg)
    
    def bulk_insert(
        self,
        table_name: str,
        columns: List[str],
        values: List[List[Any]],
        batch_size: int = 1000,
        max_workers: Optional[int] = None
    ) -> int:
        """
        Perform bulk insertion using multiple threads.
        
        Args:
            table_name: Name of the target table
            columns: List of column names
            values: List of value lists to insert
            batch_size: Number of records per batch
            max_workers: Maximum number of worker threads (default: min(32, cpu_count()*4))
        
        Returns:
            Total number of inserted rows
        """
        if not values:
            return 0
        
        def insert_batch(batch_values):
            placeholders = ','.join(['%s'] * len(columns))
            insert_sql = f"""
            INSERT INTO {table_name} ({','.join(columns)})
            VALUES ({placeholders})
            """
            return self.execute(insert_sql, batch_values)
        
        # Split values into batches
        batches = [values[i:i + batch_size] for i in range(0, len(values), batch_size)]
        total_rows = 0
        
        # Use ThreadPoolExecutor for parallel insertion
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(insert_batch, batch) for batch in batches]
            for future in futures:
                total_rows += future.result()
        
        return total_rows
    
    def close(self) -> None:
        """Close all database connections in the pool."""
        if self._pool is not None:
            if self.logging_enabled:
                logger.info("Closing database connection pool")
            self._pool.closeall()
            self._pool = None 