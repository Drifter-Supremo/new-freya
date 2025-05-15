import psycopg2
from dotenv import load_dotenv
import os

def test_connection():
    load_dotenv()
    sqlalchemy_url = os.getenv("POSTGRES_URL")
    
    # Convert SQLAlchemy URL to psycopg2 format
    if sqlalchemy_url and sqlalchemy_url.startswith('postgresql+psycopg2://'):
        db_url = sqlalchemy_url.replace('postgresql+psycopg2://', 'postgresql://')
    else:
        db_url = sqlalchemy_url
    
    if not db_url:
        print("❌ POSTGRES_URL not found in .env file")
        return
    
    print(f"🔍 Testing connection to: {db_url.split('@')[-1]}")
    
    try:
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        
        print(f"✅ Connected to PostgreSQL {db_version[0]}")
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'freya_dev_db'")
        db_exists = cursor.fetchone()
        print(f"📊 Database 'freya_dev_db' exists: {'✅ Yes' if db_exists else '❌ No'}")
        
        # List all databases (if you have permissions)
        try:
            cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
            print("\n📋 Available databases:")
            for db in cursor.fetchall():
                print(f"- {db[0]}")
        except Exception as e:
            print(f"\nℹ️ Couldn't list databases (permission issue): {e}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\nTroubleshooting steps:")
        print("1. Verify PostgreSQL service is running")
        print("2. Check if the credentials in .env file are correct")
        print("3. Ensure the database 'freya_dev_db' exists")
        print("4. Check if the user 'freya_user' has proper permissions")

if __name__ == "__main__":
    test_connection()
