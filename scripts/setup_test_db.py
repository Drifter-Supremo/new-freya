import os
import sys
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

def setup_test_database():
    # Load environment variables
    load_dotenv()
    
    # Get database connection parameters from .env
    db_url = os.getenv("POSTGRES_URL")
    if not db_url:
        print("Error: POSTGRES_URL not found in .env file")
        return False
    
    # Parse the connection string
    if db_url.startswith('postgresql+psycopg2://'):
        db_url = db_url.replace('postgresql+psycopg2://', 'postgresql://')
    
    # Extract connection parameters
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
    
    test_db_name = 'freya_test_db'
    
    try:
        # Connect to PostgreSQL server
        print(f"Connecting to PostgreSQL server at {db_params['host']}:{db_params['port']}...")
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if test database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (test_db_name,))
        exists = cursor.fetchone()
        
        if exists:
            print(f"Database '{test_db_name}' already exists. Dropping it...")
            # Terminate existing connections to the database
            cursor.execute(f"""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = '{test_db_name}'
                AND pid <> pg_backend_pid();
            """)
            cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
            print(f"Dropped database '{test_db_name}'")
        
        # Create the test database
        print(f"Creating database '{test_db_name}'...")
        cursor.execute(f"CREATE DATABASE {test_db_name}")
        print(f"Created database '{test_db_name}'")
        
        # Close the cursor and connection
        cursor.close()
        conn.close()
        
        # Update .env.test with the test database URL
        test_db_url = f"postgresql://{user_pass[0]}:{user_pass[1] if len(user_pass) > 1 else ''}@{host_port[0]}:{host_port[1] if len(host_port) > 1 else '5432'}/{test_db_name}"
        with open('.env.test', 'w') as f:
            f.write(f"TEST_DATABASE_URL={test_db_url}\n")
            f.write("ENVIRONMENT=test\n")
        
        print("\n✅ Test database setup complete!")
        print(f"Updated .env.test with connection details for database '{test_db_name}'")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if setup_test_database():
        print("\nYou can now run tests with: pytest tests/")
    else:
        print("\nFailed to set up test database. Please check the error message above.")
        sys.exit(1)
