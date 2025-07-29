"""Custom exceptions for PostgreSQL operations."""

class PostgresError(Exception):
    """Base exception for PostgreSQL operations."""
    pass

class ConnectionError(PostgresError):
    """Raised when there's an error establishing database connection."""
    pass

class QueryError(PostgresError):
    """Raised when there's an error executing a query."""
    pass

class ConfigurationError(PostgresError):
    """Raised when there's an error in configuration."""
    pass 