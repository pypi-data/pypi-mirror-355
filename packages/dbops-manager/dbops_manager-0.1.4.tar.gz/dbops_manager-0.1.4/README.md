# dbops-manager

A lightweight PostgreSQL operations manager optimized for AWS Lambda environments. This package provides a simple, efficient interface for PostgreSQL database operations with proper connection management and error handling.

## Features

- Lightweight PostgreSQL operations with minimal dependencies
- Environment variable and dictionary-based configuration
- Connection pooling optimization for AWS Lambda
- Comprehensive error handling and logging
- Support for parameterized queries
- Dictionary result format support
- Stateless operation model

## Installation

```bash
pip install dbops-manager
```

## Quick Start

### Using Environment Variables

```python
from dbops_manager import PostgresOps

# Initialize with environment variables
# Required env vars: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
db = PostgresOps.from_env(logging_enabled=True)

# Execute a query
results = db.fetch("SELECT * FROM users WHERE active = %s", [True])

# Don't forget to close the connection
db.close()
```

### Using Configuration Dictionary

```python
from dbops_manager import PostgresOps

config = {
    'host': 'localhost',
    'port': '5432',
    'dbname': 'example',
    'user': 'postgres',
    'password': 'postgres'
}

db = PostgresOps.from_config(config, logging_enabled=True)
```

## Complete Example

Here's a complete example demonstrating table creation, data insertion, and querying:

```python
import logging
from dbops_manager import PostgresOps, QueryError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def create_test_table(db: PostgresOps) -> None:
    """Create a test table if it doesn't exist."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS test_users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(255) UNIQUE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    )
    """
    db.execute(create_table_sql)

def insert_test_data(db: PostgresOps) -> None:
    """Insert test data into the table."""
    users = [
        ("John Doe", "john@example.com"),
        ("Jane Smith", "jane@example.com"),
        ("Bob Wilson", "bob@example.com")
    ]
    
    insert_sql = """
    INSERT INTO test_users (name, email)
    VALUES (%s, %s)
    ON CONFLICT (email) DO NOTHING
    RETURNING id, name, email
    """
    
    for user in users:
        try:
            result = db.fetch(insert_sql, list(user))
            if result:
                print(f"Inserted user: {result[0]}")
            else:
                print(f"User with email {user[1]} already exists")
        except QueryError as e:
            print(f"Error inserting user {user}: {e}")

def main():
    config = {
        'host': 'localhost',
        'port': '5432',
        'dbname': 'example',
        'user': 'postgres',
        'password': 'postgres'
    }
    
    try:
        # Initialize database connection
        db = PostgresOps.from_config(config, logging_enabled=True)
        
        # Create table
        create_test_table(db)
        
        # Insert data
        insert_test_data(db)
        
        # Query all users
        all_users = db.fetch("SELECT * FROM test_users ORDER BY id")
        for user in all_users:
            print(f"User {user['id']}: {user['name']} ({user['email']})")
    
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main()
```

## API Reference

### PostgresOps Class

#### Class Methods

- `from_env(env_prefix="DB_", logging_enabled=False)`: Create instance from environment variables
- `from_config(config: Dict[str, str], logging_enabled=False)`: Create instance from configuration dictionary

#### Instance Methods

- `fetch(query: str, params: Optional[List[Any]] = None, as_dict: bool = True)`: Execute SELECT query and return results
- `execute(query: str, params: Optional[List[Any]] = None)`: Execute modification query (INSERT/UPDATE/DELETE)
- `close()`: Close database connection

### Environment Variables

When using `from_env()`, the following environment variables are required:
- `DB_HOST`: Database host
- `DB_PORT`: Database port (default: 5432)
- `DB_NAME`: Database name
- `DB_USER`: Database user
- `DB_PASSWORD`: Database password
- `DB_SSLMODE`: SSL mode (optional, default: prefer)

## Error Handling

The package provides custom exceptions for better error handling:

```python
from dbops_manager import PostgresError, ConnectionError, QueryError, ConfigurationError

try:
    db = PostgresOps.from_env()
    results = db.fetch("SELECT * FROM users")
except ConnectionError as e:
    print(f"Failed to connect: {e}")
except QueryError as e:
    print(f"Query failed: {e}")
except ConfigurationError as e:
    print(f"Invalid configuration: {e}")
except PostgresError as e:
    print(f"General database error: {e}")
```

## AWS Lambda Usage

The package is optimized for AWS Lambda environments. Example Lambda function:

```python
from dbops_manager import PostgresOps

def lambda_handler(event, context):
    try:
        db = PostgresOps.from_env()
        results = db.fetch("SELECT * FROM users")
        return {
            'statusCode': 200,
            'body': results
        }
    finally:
        db.close()
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 