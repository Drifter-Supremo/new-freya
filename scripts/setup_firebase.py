#!/usr/bin/env python
"""
setup_firebase.py - Helper script to set up Firebase integration

This script installs required dependencies, sets up environment variables,
and tests the Firebase connection.
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def print_header(title):
    """Print a header with the given title."""
    print("\n" + "=" * 60)
    print(f" {title} ".center(60, "="))
    print("=" * 60 + "\n")

def install_dependencies():
    """Install required dependencies for Firebase integration."""
    print_header("Installing Dependencies")
    
    dependencies = [
        "firebase-admin>=6.2.0",
        "google-cloud-firestore>=2.11.0"
    ]
    
    print("Installing the following packages:")
    for dep in dependencies:
        print(f"- {dep}")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + dependencies)
        print("\n✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error installing dependencies: {e}")
        return False

def setup_env_file():
    """Set up the .env file with Firebase configuration."""
    print_header("Setting Up Environment Variables")
    
    # Check if .env.firebase exists
    env_template = Path(".env.firebase")
    env_file = Path(".env")
    
    if not env_template.exists():
        print(f"❌ Template file {env_template} not found")
        return False
    
    # Check if .env already exists
    if env_file.exists():
        overwrite = input(f"The file {env_file} already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Skipping environment setup")
            return True
    
    # Copy template to .env
    try:
        with open(env_template, 'r') as template:
            content = template.read()
        
        with open(env_file, 'w') as env:
            env.write(content)
        
        print(f"✅ Created {env_file} from template")
        print(f"⚠️  Please edit {env_file} to add your OpenAI API key")
        return True
    except Exception as e:
        print(f"❌ Error setting up environment file: {e}")
        return False

def test_firebase_connection():
    """Test the Firebase connection."""
    print_header("Testing Firebase Connection")
    
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # Get Firebase project ID from environment or use default
        from dotenv import load_dotenv
        load_dotenv()
        
        project_id = os.environ.get("FIREBASE_PROJECT_ID", "freya-ai-chat")
        
        print(f"Testing connection to Firebase project: {project_id}")
        
        # Initialize Firebase
        if not firebase_admin._apps:
            firebase_admin.initialize_app(None, {
                'projectId': project_id
            })
        
        # Try to get Firestore client
        db = firestore.client()
        
        # Attempt a simple operation
        print("Attempting to list collections...")
        collections = db.collections()
        collection_list = [c.id for c in collections]
        
        if collection_list:
            print(f"✅ Successfully connected to Firebase. Collections found: {collection_list}")
        else:
            print("✅ Connected to Firebase, but no collections found (this might be normal for a new project)")
        
        return True
    except ImportError:
        print("❌ Firebase modules not found. Make sure you ran the install step.")
        return False
    except Exception as e:
        print(f"❌ Error connecting to Firebase: {e}")
        return False

def check_openapi_key():
    """Check if OpenAI API key is set."""
    print_header("Checking OpenAI API Key")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key or api_key == "your_openai_api_key_here":
        print("❌ OpenAI API key not found or using default value")
        print("⚠️  Please set your OpenAI API key in the .env file")
        return False
    
    print("✅ OpenAI API key found")
    return True

def main():
    """Main function."""
    print_header("Firebase Integration Setup")
    
    success = True
    
    # Step 1: Install dependencies
    if not install_dependencies():
        success = False
    
    # Step 2: Set up environment file
    if not setup_env_file():
        success = False
    
    # Step 3: Test Firebase connection
    if not test_firebase_connection():
        success = False
    
    # Step 4: Check OpenAI API key
    if not check_openapi_key():
        success = False
    
    # Summary
    print_header("Setup Summary")
    if success:
        print("✅ Firebase integration setup completed successfully!")
        print("\nNext steps:")
        print("1. Make sure your OpenAI API key is set in the .env file")
        print("2. Run the server: python -m uvicorn app.main:app --reload")
        print("3. Test the API: python scripts/test_firebase_chat.py")
    else:
        print("⚠️  Firebase integration setup completed with warnings/errors.")
        print("Please fix the issues above before running the server.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())