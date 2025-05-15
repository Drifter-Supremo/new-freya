import os
import sys
import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

def create_test_database():
    # Load environment variables
    load_dotenv()
    
    # Get database connection parameters from .env file
    db_url = os.getenv('POSTGRES_URL')
    if not db_url:
        print("Error: POSTGRES_URL not found in environment variables")
        sys.exit(1)
    
    # Parse the connection string
    # Format: postgresql://username:password@host:port/dbname
    parts = db_url.split('//')[1].split('@')
    user_pass = parts[0].split(':')
    host_port_db = parts[1].split('/')
    dbname = host_port_db[1] if len(host_port_db) > 1 else 'postgres'
    host_port = host_port_db[0].split(':')
    
    db_params = {
        'dbname': 'postgres',  # Connect to default database first
        'user': user_pass[0],
        'password': user_pass[1] if len(user_pass) > 1 else '',
        'host': host_port[0],
        'port': host_port[1] if len(host_port) > 1 else '5432'
    }
    
    # Database name to create
    test_db_name = 'freya_test'
    
    try:
        # Connect to PostgreSQL server
        print(f"Connecting to PostgreSQL server at {db_params['host']}:{db_params['port']}...")
        conn = psycopg2.connect(**db_params)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (test_db_name,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"Database '{test_db_name}' already exists. Dropping it...")
            cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(test_db_name)))
            print(f"Dropped database '{test_db_name}'")
        
        # Create the test database
        print(f"Creating database '{test_db_name}'...")
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(test_db_name)))
        print(f"Created database '{test_db_name}'")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        # Update .env.test with the correct connection string
        with open('.env.test', 'w') as f:
            f.write(f"TEST_DATABASE_URL=postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{test_db_name}\n")
            f.write("ENVIRONMENT=test\n")
        
        print("\nTest database setup complete!")
        print(f"Updated .env.test with connection details for database '{test_db_name}'")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_test_database()
