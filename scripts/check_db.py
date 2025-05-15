import os
import sys
import psycopg2
from dotenv import load_dotenv

def check_database_connection():
    # Load environment variables from .env.test
    load_dotenv('.env.test')
    
    # Get database URL from environment
    db_url = os.getenv('TEST_DATABASE_URL')
    if not db_url:
        print("Error: TEST_DATABASE_URL not found in environment variables")
        return False
    
    try:
        # Parse the connection string
        # Format: postgresql://username:password@host:port/dbname
        parts = db_url.split('//')[1].split('@')
        user_pass = parts[0].split(':')
        host_port = parts[1].split('/')
        dbname = host_port[1]
        host_port = host_port[0].split(':')
        
        conn_params = {
            'dbname': dbname,
            'user': user_pass[0],
            'password': user_pass[1] if len(user_pass) > 1 else None,
            'host': host_port[0],
            'port': host_port[1] if len(host_port) > 1 else '5432'
        }
        
        # Try to connect to the database
        print(f"Connecting to database: {conn_params['dbname']} on {conn_params['host']}:{conn_params['port']}")
        conn = psycopg2.connect(**conn_params)
        print("Successfully connected to the database!")
        
        # Check if the database is empty
        cur = conn.cursor()
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cur.fetchall()
        
        if tables:
            print("\nExisting tables:")
            for table in tables:
                print(f"- {table[0]}")
        else:
            print("\nNo tables found in the database.")
            
        cur.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return False

if __name__ == "__main__":
    check_database_connection()
