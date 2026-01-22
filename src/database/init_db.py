"""
Database initialization script for MediAnalyze Pro
Creates database tables and optionally seeds with sample data
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database.connection import DatabaseConnection, get_db_connection
from src.database.models import Base


def init_database(database_url: str = None, drop_existing: bool = False):
    """
    Initialize the database by creating all tables
    
    Args:
        database_url: Optional database URL (default: uses default SQLite path)
        drop_existing: If True, drop existing tables before creating (WARNING: deletes all data!)
    """
    print("Initializing MediAnalyze Pro database...")
    
    # Get database connection
    db_conn = get_db_connection(database_url)
    
    if drop_existing:
        print("WARNING: Dropping existing tables...")
        db_conn.drop_tables()
        print("Existing tables dropped.")
    
    # Create all tables
    print("Creating database tables...")
    db_conn.create_tables()
    print("Database tables created successfully!")
    
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(db_conn.engine)
    tables = inspector.get_table_names()
    
    print(f"\nCreated {len(tables)} tables:")
    for table in sorted(tables):
        print(f"  - {table}")
    
    print("\nDatabase initialization complete!")
    return db_conn


def reset_database(database_url: str = None):
    """
    Reset the database by dropping and recreating all tables
    WARNING: This will delete all data!
    
    Args:
        database_url: Optional database URL
    """
    print("WARNING: This will delete all data in the database!")
    response = input("Are you sure you want to continue? (yes/no): ")
    
    if response.lower() == 'yes':
        init_database(database_url, drop_existing=True)
    else:
        print("Database reset cancelled.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Initialize MediAnalyze Pro database')
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Drop existing tables before creating (WARNING: deletes all data!)'
    )
    parser.add_argument(
        '--db-url',
        type=str,
        default=None,
        help='Database URL (default: uses SQLite at data/medanalyze.db)'
    )
    
    args = parser.parse_args()
    
    if args.reset:
        reset_database(args.db_url)
    else:
        init_database(args.db_url, drop_existing=False)
